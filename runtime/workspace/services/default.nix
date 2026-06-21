{
  pkgs,
  lib ? pkgs.lib,
  tty ? true,
  code ? false,
  desktop ? false,
  workspacePackages ? null,
}:

let
  desktopPackageLaunchers = workspacePackages.desktopPackageLaunchers or [ ];
in
lib.optionals tty [ (import ./tty { inherit pkgs; }) ]
++ lib.optionals code [ (import ./code { inherit pkgs; }) ]
++ lib.optionals desktop [
  (import ./desktop {
    inherit pkgs;
    packageLaunchers = desktopPackageLaunchers;
  })
]
