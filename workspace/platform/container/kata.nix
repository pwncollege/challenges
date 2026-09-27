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
    patches = [ ./firecracker-readonly.patch ];
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

  package = pkgs.stdenvNoCC.mkDerivation {
    pname = "kata-runtime-rs";
    inherit version;
    src = pkgs.fetchurl {
      url = "${release}/kata-static-${version}-amd64.tar.zst";
      hash = "sha256-uCiQT6Px5J3dfceZxyyxUDzR53LTVMOYfI1BibKmI6g=";
    };
    nativeBuildInputs = [ pkgs.zstd ];
    dontUnpack = true;
    dontFixup = true;
    installPhase = ''
      mkdir -p "$out/bin"
      tar --zstd -xf "$src" -C "$out" --strip-components=3 \
        ./opt/kata/share/defaults/kata-containers/runtime-rs/configuration-rs-fc.toml \
        ./opt/kata/share/kata-containers/kata-ubuntu-resolute.image
      mv "$out/share/kata-containers/kata-ubuntu-resolute.image" "$out/share/kata-containers/kata-containers.img"
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
  firecracker = pkgs.stdenvNoCC.mkDerivation (final: {
    pname = "firecracker";
    version = "1.17.0";
    src = pkgs.fetchurl {
      url = "https://github.com/firecracker-microvm/firecracker/releases/download/v${final.version}/firecracker-v${final.version}-x86_64.tgz";
      hash = "sha256-BglKEQiunoKqTCOndaqSdY9T8RddQiJw2dYWLLmt5Vg=";
    };
    # The jailer copies this static executable into its chroot.
    dontFixup = true;
    installPhase = ''
      install -Dm555 firecracker-v${final.version}-x86_64 "$out/bin/firecracker"
      install -Dm555 jailer-v${final.version}-x86_64 "$out/bin/jailer"
    '';
    meta = {
      license = pkgs.lib.licenses.asl20;
      platforms = [ "x86_64-linux" ];
      sourceProvenance = [ pkgs.lib.sourceTypes.binaryNativeCode ];
    };
  });
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
