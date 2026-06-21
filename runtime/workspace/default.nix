{
  pkgs,
  name ? "pwn-workspace-runtime",
  workspacePackages ? import ./packages { inherit pkgs; },
  workspaceServices ? import ./services { inherit pkgs; },
}:
let
  workspaceAgent = import ./agent { inherit pkgs; };
  workspaceProfileFiles = pkgs.runCommand "workspace-profile-files" { } ''
    install -Dm0644 ${./etc/profile.d/99-pwn-workspace.sh} $out/etc/profile.d/99-pwn-workspace.sh
  '';
in
pkgs.buildEnv {
  inherit name;

  paths =
    with pkgs;
    [
      workspaceAgent
      workspacePackages
      workspaceProfileFiles
    ]
    ++ workspaceServices;
}
