{
  pkgs,
  lib ? pkgs.lib,
  name,
  workspaceRuntime,
  containerdSockPath,
  seccompProfile,
  nixStorePath,
  daemonListenAddress,
  dataDir,
  egressAddress,
  egressServiceName,
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
      "${unitName "containerd"}.service"
      "${egressServiceName}.service"
      "${unitName "store"}.service"
    ];
    after = [
      "${unitName "containerd"}.service"
      "${egressServiceName}.service"
      "${unitName "store"}.service"
    ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${package}/bin/workspace-daemon";
      Environment = [
        "PATH=${lib.makeBinPath [ pkgs.e2fsprogs pkgs.kata-runtime ]}"
        "PWN_WORKSPACE_AGENT_PORT=8000"
        "PWN_WORKSPACE_CONTAINERD_ADDRESS=unix://${containerdSockPath}"
        "PWN_WORKSPACE_DAEMON_LISTEN_ADDRESS=${daemonListenAddress}"
        "PWN_WORKSPACE_EGRESS_ADDRESS=${egressAddress}"
        "PWN_WORKSPACE_LOG_DIRECTORY=${dataDir}/workspace-records"
        "PWN_WORKSPACE_NIX_STORE_PATH=${nixStorePath}"
        "PWN_WORKSPACE_PATH=${workspaceRuntime}"
        "PWN_WORKSPACE_SECCOMP_PROFILE=${seccompProfile}"
      ]
      ++ lib.optional (publicKey != null) "PWN_WORKSPACE_PUBLIC_KEY=${publicKey}"
      ++ lib.optional (volumeBasePath != null) "PWN_WORKSPACE_VOLUME_BASE_PATH=${volumeBasePath}";
      Restart = "on-failure";
      RestartSec = 1;
    };
  };
}
