{
  pkgs,
  lib ? pkgs.lib,
  name,
  dataDir,
  runDir,
  workspaceNetwork,
  workspaceSubnet,
}:

let
  unitName = component: "${name}-${component}";

  dockerDataDir = "${dataDir}/docker";
  dockerRunDir = "${runDir}/docker";
  dockerSockPath = "${dockerRunDir}/docker.sock";

  containerdDataDir = "${dataDir}/containerd";
  containerdRunDir = "${runDir}/containerd";
  containerdSockPath = "${containerdRunDir}/containerd.sock";

  docker = pkgs.docker;
  kataConfig = import ./kata.nix { inherit pkgs; };
  seccompProfile = import ./seccomp.nix { inherit pkgs; };

  jsonFormat = pkgs.formats.json { };
  dockerDaemonJson = jsonFormat.generate "${name}-docker-daemon.json" {
    "data-root" = dockerDataDir;
    "exec-root" = dockerRunDir;
    "pidfile" = "${dockerRunDir}/dockerd.pid";
    "log-driver" = "journald";
    "seccomp-profile" = "${seccompProfile}";
    "containerd" = containerdSockPath;

    "features" = {
      "containerd-snapshotter" = true;
      "time-namespaces" = false;
    };

    "runtimes" = {
      "kata" = {
        "runtimeType" = "${pkgs.kata-runtime}/bin/containerd-shim-kata-v2";
        "options" = {
          "ConfigPath" = "${kataConfig}";
        };
      };
    };
  };

  containerdConfig = pkgs.writeText "${name}-containerd-config.toml" ''
    version = 2
    root = "${containerdDataDir}"
    state = "${containerdRunDir}"

    [grpc]
      address = "${containerdSockPath}"
  '';

  workspaceNetworkLabel = "pwn.workspace-network";
  networkSetup = pkgs.writeShellScript "${name}-network-setup" ''
    set -euo pipefail
    export DOCKER_HOST=${lib.escapeShellArg "unix://${dockerSockPath}"}
    if ! ${docker}/bin/docker network inspect ${lib.escapeShellArg workspaceNetwork} >/dev/null 2>&1; then
      ${docker}/bin/docker network create \
        --driver bridge \
        --subnet ${lib.escapeShellArg workspaceSubnet} \
        --label ${lib.escapeShellArg "${workspaceNetworkLabel}=true"} \
        ${lib.escapeShellArg workspaceNetwork} >/dev/null
    fi
  '';

  serviceCommon = {
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "notify";
      Restart = "on-failure";
      TimeoutStartSec = 0;
      Delegate = true;
      KillMode = "process";
      LimitNPROC = "infinity";
      LimitCORE = "infinity";
      TasksMax = "infinity";
      OOMScoreAdjust = -500;
    };
  };
in
{
  inherit
    dockerDataDir
    dockerRunDir
    dockerSockPath
    containerdDataDir
    containerdRunDir
    containerdSockPath
    ;

  services = {
    "${unitName "containerd"}" = lib.recursiveUpdate serviceCommon {
      description = "pwn.college challenge runtime containerd";
      after = [ "local-fs.target" ];
      serviceConfig = {
        ExecStart = "${pkgs.containerd}/bin/containerd --config ${containerdConfig}";
        Environment = "PATH=${pkgs.runc}/bin";
        NotifyAccess = "all";
        TimeoutStartSec = 60;
      };
    };

    "${unitName "docker"}" = lib.recursiveUpdate serviceCommon {
      description = "pwn.college challenge runtime Docker daemon";
      requires = [
        "${unitName "docker"}.socket"
        "${unitName "containerd"}.service"
      ];
      after = [
        "local-fs.target"
        "${unitName "containerd"}.service"
      ];
      serviceConfig.ExecStart = "${docker}/bin/dockerd --config-file=${dockerDaemonJson} -H fd://";
    };

    "${unitName "network"}" = {
      description = "pwn.college workspace Docker network";
      requires = [ "${unitName "docker"}.service" ];
      after = [ "${unitName "docker"}.service" ];
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        Type = "oneshot";
        ExecStart = networkSetup;
        RemainAfterExit = true;
      };
    };
  };

  sockets = {
    "${unitName "docker"}" = {
      description = "pwn.college challenge runtime Docker socket";
      wantedBy = [ "sockets.target" ];
      socketConfig = {
        ListenStream = dockerSockPath;
        SocketMode = "0666";
      };
    };
  };

  tmpfilesRules = [
    "d ${dockerRunDir} 0711 root root -"
    "d ${dockerDataDir} 0711 root root -"
    "d ${containerdRunDir} 0711 root root -"
    "d ${containerdDataDir} 0711 root root -"
  ];
}
