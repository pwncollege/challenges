{ pkgs }:
let
  workspaceAgent = import ./agent { inherit pkgs; };

  workspaceServices = [
    (import ./services/code { inherit pkgs; })
    (import ./services/desktop { inherit pkgs; })
    (import ./services/tty { inherit pkgs; })
  ];
in
pkgs.buildEnv {
  name = "pwn-workspace-runtime";

  paths =
    with pkgs;
    [
      workspaceAgent
      curl
    ]
    ++ workspaceServices;
}
