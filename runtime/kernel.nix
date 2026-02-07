{ pkgs, name }:
let
  kataContainersSrc = pkgs.fetchzip {
    url = "https://github.com/kata-containers/kata-containers/archive/refs/tags/${pkgs.kata-runtime.version}.tar.gz";
    hash = "sha256-+SppAF77NbXlSrBGvIm40AmNC12GrexbX7fAPBoDAcs=";
  };

  # Dojo-style: derive kernel version from Kata's versions.yaml via yq.
  # This uses import-from-derivation (IFD): evaluation reads the derivation output.
  kernelVersionRaw =
    pkgs.lib.strings.trim (builtins.readFile "${pkgs.runCommand "${name}-kata-kernel-version" { nativeBuildInputs = [ pkgs.yq ]; } ''
      mkdir -p "$out"
      yq -r '.assets.kernel.version' ${kataContainersSrc}/versions.yaml > "$out/version"
    ''}/version");

  kernelVersion =
    if pkgs.lib.hasPrefix "v" kernelVersionRaw then
      pkgs.lib.removePrefix "v" kernelVersionRaw
    else
      kernelVersionRaw;

  kernelMajor = builtins.elemAt (pkgs.lib.splitString "." kernelVersion) 0;
  kernelTarball = pkgs.fetchurl {
    url = "http://cdn.kernel.org/pub/linux/kernel/v${kernelMajor}.x/linux-${kernelVersion}.tar.xz";
    hash = "sha256-q0iACrSZhaeNIxiuisXyj9PhI+oXNX7yFJgQWlMzczY=";
  };

  dojoFragment = ''
CONFIG_SECURITY_LANDLOCK=y

CONFIG_BPF_JIT=y
CONFIG_BPF_SYSCALL=y
CONFIG_BPF=y
CONFIG_DEBUG_KERNEL=y
CONFIG_DEBUG_INFO_DWARF4=y
CONFIG_DEBUG_INFO_BTF=y
CONFIG_DYNAMIC_FTRACE=y
CONFIG_FTRACE=y
CONFIG_FUNCTION_TRACER=y
CONFIG_KPROBE_EVENTS=y
CONFIG_KPROBES=y
CONFIG_PERF_EVENTS=y
CONFIG_PROFILING=y
'';
in
pkgs.stdenv.mkDerivation {
  pname = "${name}-kata-kernel";
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

    for arch in x86_64 arm64; do
cat > "configs/fragments/$arch/zz-dojo.conf" <<'EOF'
${dojoFragment}
EOF
    done

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
