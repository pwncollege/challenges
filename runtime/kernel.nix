{ pkgs, name }:
let
  kataContainersSrc = pkgs.fetchzip {
    url = "https://github.com/kata-containers/kata-containers/archive/refs/tags/${pkgs.kata-runtime.version}.tar.gz";
    hash = "sha256-+SppAF77NbXlSrBGvIm40AmNC12GrexbX7fAPBoDAcs=";
  };

  kernelVersion = builtins.readFile "${pkgs.runCommand "kata-kernel-version"
    { nativeBuildInputs = [ pkgs.yq ]; }
    ''
      version="$(yq -r '.assets.kernel.version' ${kataContainersSrc}/versions.yaml)"
      printf '%s' "''${version#v}" > "$out"
    ''
  }";
  kernelMajor = builtins.elemAt (pkgs.lib.splitString "." kernelVersion) 0;
  kernelTarball = pkgs.fetchurl {
    url = "http://cdn.kernel.org/pub/linux/kernel/v${kernelMajor}.x/linux-${kernelVersion}.tar.xz";
    hash = "sha256-q0iACrSZhaeNIxiuisXyj9PhI+oXNX7yFJgQWlMzczY=";
  };

  config =
    let
      enable = [
        "SECURITY_LANDLOCK"
        "BPF_JIT"
        "BPF_SYSCALL"
        "BPF"
        "DEBUG_KERNEL"
        "DEBUG_INFO_DWARF4"
        "DEBUG_INFO_BTF"
        "DYNAMIC_FTRACE"
        "FTRACE"
        "FUNCTION_TRACER"
        "KPROBE_EVENTS"
        "KPROBES"
        "PERF_EVENTS"
        "PROFILING"
      ];
    in
    pkgs.writeText "${name}.conf" (pkgs.lib.strings.concatLines (map (t: "CONFIG_${t}=y") enable));
in
pkgs.stdenv.mkDerivation {
  pname = "${name}-linux-kernel";
  version = kernelVersion;
  dontUnpack = true;
  buildInputs = with pkgs; [
    zlib
  ];
  nativeBuildInputs = with pkgs; [
    bc
    bison
    coreutils
    cpio
    elfutils
    flex
    gawk
    gcc
    gnumake
    gnugrep
    gnutar
    gzip
    kmod
    ncurses
    openssl
    pahole
    perl
    pkg-config
    python3
    rsync
    util-linux
    xz
  ];
  buildPhase = ''
    runHook preBuild

    export SOURCE_DATE_EPOCH=1
    export KBUILD_BUILD_TIMESTAMP="1970-01-01T00:00:01Z"
    export KBUILD_BUILD_USER="nix"
    export KBUILD_BUILD_HOST="nix"

    mkdir -p tools
    cp -R ${kataContainersSrc}/tools/packaging tools/packaging
    chmod -R u+w tools/packaging
    patchShebangs tools/packaging
    cd tools/packaging/kernel

    install -D -m 0644 ${config} configs/fragments/x86_64/${name}.conf

    cp ${kernelTarball} linux-${kernelVersion}.tar.xz
    sha256sum linux-${kernelVersion}.tar.xz > linux-${kernelVersion}.tar.xz.sha256

    DESTDIR="$out" PREFIX="/" ./build-kernel.sh -v "${kernelVersion}" setup
    patchShebangs kata-linux-${kernelVersion}-*/scripts kata-linux-${kernelVersion}-*/tools
    DESTDIR="$out" PREFIX="/" ./build-kernel.sh -v "${kernelVersion}" build
    DESTDIR="$out" PREFIX="/" ./build-kernel.sh -v "${kernelVersion}" install

    runHook postBuild
  '';
  installPhase = "true";
}
