{ pkgs }:
let
  python = pkgs.python3.withPackages (
    ps: with ps; [
      flask
      pexpect
      pwntools
      pycryptodome
      requests
      scapy
    ]
  );
in
pkgs.buildEnv {
  name = "workspace-packages";

  paths = with pkgs; [
    bashInteractive
    cacert
    glibcLocales
    man
    man-pages
    ncurses
    python
  ];

  passthru = {
    desktopPackageLaunchers = [ ];
    inherit python;
  };
}
