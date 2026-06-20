{ pkgs }:
let
  python = pkgs.python3.withPackages (
    ps: with ps; [
      pwntools
    ]
  );
in
pkgs.buildEnv {
  name = "workspace-packages";

  paths = [ python ];

  passthru = {
    inherit python;
  };
}
