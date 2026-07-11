{
  pkgs,
  lib ? pkgs.lib,
  name,
  workspaceRuntime,
  dockerSockPath,
  nixStorePath,
  daemonListenAddress,
  workspaceNetwork,
  publicKey ? null,
  volumeBasePath ? null,
}:

let
  package = import ./package.nix { inherit pkgs; };
  unitName = component: "${name}-${component}";
in
{
  url = "http://${daemonListenAddress}";

  service = {
    description = "pwn.college workspace daemon";
    requires = [
      "${unitName "network"}.service"
      "${unitName "store"}.service"
    ];
    after = [
      "${unitName "network"}.service"
      "${unitName "store"}.service"
    ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${package}/bin/workspace-daemon";
      Environment = [
        "DOCKER_HOST=unix://${dockerSockPath}"
        "PATH=${lib.makeBinPath [ pkgs.btrfs-progs ]}"
        "PWN_WORKSPACE_AGENT_PORT=8000"
        "PWN_WORKSPACE_DAEMON_LISTEN_ADDRESS=${daemonListenAddress}"
        "PWN_WORKSPACE_DOCKER_NETWORK=${workspaceNetwork}"
        "PWN_WORKSPACE_NIX_STORE_PATH=${nixStorePath}"
        "PWN_WORKSPACE_PATH=${workspaceRuntime}"
      ]
      ++ lib.optional (publicKey != null) "PWN_WORKSPACE_PUBLIC_KEY=${publicKey}"
      ++ lib.optional (volumeBasePath != null) "PWN_WORKSPACE_VOLUME_BASE_PATH=${volumeBasePath}";
      Restart = "on-failure";
      RestartSec = 1;
    };
  };
}
