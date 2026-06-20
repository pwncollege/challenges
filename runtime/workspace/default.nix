{
  pkgs,
  name ? "pwn-workspace-runtime",
  workspacePackages ? import ./packages { inherit pkgs; },
  workspaceServices ? import ./services { inherit pkgs; },
}:
let
  workspaceAgent = import ./agent { inherit pkgs; };
in
pkgs.buildEnv {
  inherit name;

  paths =
    with pkgs;
    [
      workspaceAgent
      workspacePackages
    ]
    ++ workspaceServices;
}
