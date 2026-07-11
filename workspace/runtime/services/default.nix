{
  pkgs,
  lib ? pkgs.lib,
  terminal ? true,
  code ? false,
  desktop ? false,
  workspacePackages ? null,
}:

let
  desktopPackageLaunchers = workspacePackages.desktopPackageLaunchers or [ ];
in
lib.optionals terminal [ (import ./terminal { inherit pkgs; }) ]
++ lib.optionals code [ (import ./code { inherit pkgs; }) ]
++ lib.optionals desktop [
  (import ./desktop {
    inherit pkgs;
    packageLaunchers = desktopPackageLaunchers;
  })
]
