{ pkgs }:

let
  version = "4.2.0";
  release = "https://github.com/kata-containers/kata-containers/releases/download/${version}";
  source = pkgs.fetchzip {
    url = "https://github.com/kata-containers/kata-containers/archive/refs/tags/${version}.tar.gz";
    hash = "sha256-afEm5lcXD4qC2Ezhx7wyZXD5pj4uLPoSnJrvFJL+7qU=";
  };
  shim = pkgs.rustPlatform.buildRustPackage {
    pname = "kata-shim";
    inherit version;
    src = source;
    cargoHash = "sha256-wbMkdNZwvqjey33//iLUG7cVeO+iEexsDVmIW4gvV0o=";
    patches = [
      ./kata-firecracker.patch
    ];
    cargoBuildFlags = [
      "-p"
      "runtime-rs"
      "--bin"
      "containerd-shim-kata-v2"
    ];
    nativeBuildInputs = [
      pkgs.pkg-config
      pkgs.protobuf
    ];
    buildInputs = [
      pkgs.openssl
      pkgs.libseccomp
    ];
    env.RUNTIME_VERSION = version;
    preBuild = ''
      substitute src/runtime-rs/crates/shim/src/config.rs.in src/runtime-rs/crates/shim/src/config.rs \
        --replace-fail @PROJECT_NAME@ "Kata Containers" \
        --replace-fail @RUNTIME_VERSION@ "${version}" \
        --replace-fail @COMMIT@ "${version}" \
        --replace-fail @RUNTIME_NAME@ "containerd-shim-kata-v2" \
        --replace-fail @CONTAINERD_RUNTIME_NAME@ "io.containerd.kata.v2" \
        --replace-fail @BINDIR@ "$out/bin"
    '';
    # Runtime integration is exercised against real KVM by the workspace E2E suite.
    doCheck = false;
  };

  agent = pkgs.pkgsStatic.rustPlatform.buildRustPackage {
    pname = "kata-agent";
    inherit version;
    src = source;
    cargoHash = "sha256-wbMkdNZwvqjey33//iLUG7cVeO+iEexsDVmIW4gvV0o=";
    patches = [ ./kata-agent-erofs.patch ];
    cargoBuildFlags = [
      "-p"
      "kata-agent"
    ];
    buildFeatures = [ "seccomp" ];
    nativeBuildInputs = [
      pkgs.pkg-config
      pkgs.protobuf
      pkgs.rustPlatform.bindgenHook
    ];
    buildInputs = [
      pkgs.pkgsStatic.openssl
      pkgs.pkgsStatic.libseccomp
    ];
    preBuild = ''
      substitute src/agent/src/version.rs.in src/agent/src/version.rs \
        --replace-fail @AGENT_VERSION@ "${version}" \
        --replace-fail @API_VERSION@ "0.0.1" \
        --replace-fail @VERSION_COMMIT@ "${version}" \
        --replace-fail @COMMIT@ "${version}" \
        --replace-fail @AGENT_NAME@ "kata-agent" \
        --replace-fail @BINDIR@ "/usr/bin"
    '';
    # Agent behavior is exercised in the actual Firecracker guest by E2E tests.
    doCheck = false;
  };

  package = pkgs.stdenvNoCC.mkDerivation {
    pname = "kata-runtime-rs";
    inherit version;
    src = pkgs.fetchurl {
      url = "${release}/kata-static-${version}-amd64.tar.zst";
      hash = "sha256-uCiQT6Px5J3dfceZxyyxUDzR53LTVMOYfI1BibKmI6g=";
    };
    nativeBuildInputs = [
      pkgs.zstd
      pkgs.e2fsprogs
      pkgs.util-linux
      pkgs.jq
    ];
    dontUnpack = true;
    dontFixup = true;
    installPhase = ''
      mkdir -p "$out/bin"
      tar --zstd -xf "$src" -C "$out" --strip-components=3 \
        ./opt/kata/share/defaults/kata-containers/runtime-rs/configuration-rs-fc.toml \
        ./opt/kata/share/kata-containers/kata-ubuntu-resolute.image
      mv "$out/share/kata-containers/kata-ubuntu-resolute.image" "$out/share/kata-containers/kata-containers.img"
      # Replace only the agent in the matching upstream guest filesystem.
      image="$out/share/kata-containers/kata-containers.img"
      read -r offset length < <(sfdisk --json "$image" | jq -r '.partitiontable.partitions[0] | "\(.start * 512) \(.size * 512)"')
      dd if="$image" of=guest.ext4 bs=4M skip="$offset" count="$length" iflag=skip_bytes,count_bytes status=none
      debugfs -w -R 'rm /usr/bin/kata-agent' guest.ext4
      debugfs -w -R 'write ${agent}/bin/kata-agent /usr/bin/kata-agent' guest.ext4
      debugfs -w -R 'set_inode_field /usr/bin/kata-agent mode 0100755' guest.ext4
      debugfs -R 'dump /usr/bin/kata-agent check-agent' guest.ext4
      cmp check-agent ${agent}/bin/kata-agent
      e2fsck -fn guest.ext4
      dd if=guest.ext4 of="$image" bs=4M seek="$offset" oflag=seek_bytes conv=notrunc status=none
      ln -s ${shim}/bin/containerd-shim-kata-v2 "$out/bin/containerd-shim-kata-v2"
      test -s "$out/share/kata-containers/kata-containers.img"
    '';
    meta = {
      description = "Kata Containers Rust runtime and matching guest image";
      license = pkgs.lib.licenses.asl20;
      platforms = [ "x86_64-linux" ];
      sourceProvenance = [ pkgs.lib.sourceTypes.binaryNativeCode ];
    };
  };

  kernel = import ./kernel.nix {
    inherit pkgs;
    kataContainersSrc = source;
  };
  firecracker = pkgs.pkgsStatic.firecracker.overrideAttrs (
    final: old: {
      version = "1.17.0";
      src = pkgs.fetchzip {
        url = "https://github.com/firecracker-microvm/firecracker/archive/refs/tags/v1.17.0.tar.gz";
        hash = "sha256-1HL13XL8CvwGTcm8uIJxgW31hUXXLZ8F2+jV7FEgxEY=";
      };
      # Drop after upgrading to a version containing Firecracker PR #5741:
      # https://github.com/firecracker-microvm/firecracker/pull/5741
      patches = [ ./firecracker-vmdk.patch ];
      cargoDeps = pkgs.rustPlatform.fetchCargoVendor {
        inherit (final) src patches;
        name = "firecracker-1.17.0-vendor";
        hash = "sha256-PviKpDMqjhPFdViEDuPKa57oaDSjOxG/QVSvOyoCVRM=";
      };
      cargoBuildFlags = [
        "-p"
        "firecracker"
        "-p"
        "jailer"
      ];
    }
  );
  python = pkgs.python3.withPackages (p: [ p.toml ]);
  config = pkgs.runCommand "pwn-workspace-kata-config.toml" { nativeBuildInputs = [ python ]; } ''
    python - "$out" <<'PY'
    import sys
    import toml

    config = toml.load("${package}/share/defaults/kata-containers/runtime-rs/configuration-rs-fc.toml")
    config["hypervisor"]["firecracker"].update(
        path="${firecracker}/bin/firecracker",
        jailer_path="${firecracker}/bin/jailer",
        kernel="${kernel}/share/kata-containers/vmlinux.container",
        image="${package}/share/kata-containers/kata-containers.img",
        valid_hypervisor_paths=["${firecracker}/bin/firecracker"],
        valid_jailer_paths=["${firecracker}/bin/jailer"],
    )
    config["agent"]["kata"].update(dial_timeout_ms=10, reconnect_timeout_ms=3000)
    with open(sys.argv[1], "w") as output:
        toml.dump(config, output)
    PY
  '';
in
{
  inherit package config;
}
