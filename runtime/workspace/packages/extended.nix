{
  pkgs,
  desktop ? false,
}:
let
  skippedDojoPackages = [
    "angr"
    "angr-management"
  ];

  python = pkgs.python3.withPackages (
    ps: with ps; [
      asteval
      flask
      ipython
      jupyter
      pillow
      psutil
      pwntools
      pycryptodome
      pyroute2
      r2pipe
      requests
      ropper
      scapy
      selenium
    ]
  );

  desktopPackages = with pkgs; [
    cutter
    firefox
    geckodriver
    ghidra
    (lib.hiPrio wireshark)
  ];
  desktopPackageLaunchers = [
    "firefox.desktop"
    "ghidra.desktop"
    "org.wireshark.Wireshark.desktop"
  ];
in
pkgs.buildEnv {
  name = "workspace-packages-extended";

  paths =
    with pkgs;
    [
      (lib.hiPrio gcc)
      (lib.lowPrio clang)
      aflplusplus
      atuin
      bashInteractive
      bat
      bottom
      broot
      cacert
      clang-tools
      cmake
      coreutils
      curl
      delta
      dust
      emacs
      eza
      fd
      file
      findutils
      fish
      fzf
      gawk
      gdb
      gef
      glibc
      glibc.static
      glibcLocales
      gnumake
      gnugrep
      gnused
      gnutar
      gzip
      hexyl
      hostname
      htop
      hyperfine
      iproute2
      kitty.terminfo
      less
      ltrace
      man
      man-pages
      man-pages-posix
      nano
      nasm
      ncdu
      ncurses
      netcat-openbsd
      nettools
      neovim
      nmap
      nushell
      openssh
      procps
      python
      qemu
      radare2
      rappel
      ripgrep
      ripgrep-all
      ruff
      rustup
      rsync
      sage
      screen
      sd
      starship
      strace
      tcpdump
      termshark
      tmux
      tshark
      ty
      unzip
      util-linux
      vim
      wget
      which
      zellij
      zip
      zoxide
      zsh
    ]
    ++ pkgs.lib.optionals desktop desktopPackages;

  passthru = {
    inherit
      desktopPackages
      desktopPackageLaunchers
      python
      skippedDojoPackages
      ;
  };
}
