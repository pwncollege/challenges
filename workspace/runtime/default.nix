{
  pkgs,
  name ? "pwn-workspace-runtime",
  workspacePackages ? import ./packages { inherit pkgs; },
  runtimeServices ? import ./services { inherit pkgs; },
}:
let
  workspaceAgent = import ./agent { inherit pkgs; };
  workspaceProfileFiles = pkgs.runCommand "workspace-profile-files" { } ''
    install -Dm0644 ${./etc/profile.d/99-pwn-workspace.sh} $out/etc/profile.d/99-pwn-workspace.sh
    mkdir -p $out/etc/ssl/certs
    cat \
      ${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt \
      ${./etc/ssl/certs/egress-ca.pem} \
      > $out/etc/ssl/certs/workspace-ca-bundle.crt
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
    ++ runtimeServices;
}
