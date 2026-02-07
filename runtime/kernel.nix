{ pkgs, name }:
let
  kataContainersSrc = pkgs.fetchzip {
    url = "https://github.com/kata-containers/kata-containers/archive/refs/tags/${pkgs.kata-runtime.version}.tar.gz";
    hash = "sha256-+SppAF77NbXlSrBGvIm40AmNC12GrexbX7fAPBoDAcs=";
  };

  kernelVersion = "6.12.22";
  kernelTarball = pkgs.fetchurl {
    url = "https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-${kernelVersion}.tar.xz";
    hash = "sha256-q0iACrSZhaeNIxiuisXyj9PhI+oXNX7yFJgQWlMzczY=";
  };
in
pkgs.stdenv.mkDerivation {
  pname = "${name}-kata-kernel";
  version = kernelVersion;
  dontUnpack = true;
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

    cat > configs/fragments/x86_64/dojo.conf <<'EOF'
    CONFIG_SECURITY_LANDLOCK=y

    CONFIG_BPF_JIT=y
    CONFIG_BPF_SYSCALL=y
    CONFIG_BPF=y
    CONFIG_EXPERT=y
    CONFIG_DEBUG_KERNEL=y
    CONFIG_DEBUG_INFO=y
    CONFIG_DEBUG_INFO_BTF=y
    CONFIG_DYNAMIC_FTRACE=y
    CONFIG_FTRACE=y
    CONFIG_FUNCTION_TRACER=y
    CONFIG_KPROBE_EVENTS=y
    CONFIG_KPROBES=y
    CONFIG_PERF_EVENTS=y
    CONFIG_PROFILING=y
    EOF

    cat > configs/fragments/arm64/dojo.conf <<'EOF'
    CONFIG_SECURITY_LANDLOCK=y

    CONFIG_BPF_JIT=y
    CONFIG_BPF_SYSCALL=y
    CONFIG_BPF=y
    CONFIG_EXPERT=y
    CONFIG_DEBUG_KERNEL=y
    CONFIG_DEBUG_INFO=y
    CONFIG_DEBUG_INFO_BTF=y
    CONFIG_DYNAMIC_FTRACE=y
    CONFIG_FTRACE=y
    CONFIG_FUNCTION_TRACER=y
    CONFIG_KPROBE_EVENTS=y
    CONFIG_KPROBES=y
    CONFIG_PERF_EVENTS=y
    CONFIG_PROFILING=y
    EOF

    cp ${kernelTarball} linux-${kernelVersion}.tar.xz
    sha256sum linux-${kernelVersion}.tar.xz > linux-${kernelVersion}.tar.xz.sha256

    DESTDIR="$out" PREFIX="/" ./build-kernel.sh -s -v "${kernelVersion}" setup
    DESTDIR="$out" PREFIX="/" ./build-kernel.sh -v "${kernelVersion}" build
    DESTDIR="$out" PREFIX="/" ./build-kernel.sh -v "${kernelVersion}" install

    runHook postBuild
  '';
  installPhase = "true";
}
