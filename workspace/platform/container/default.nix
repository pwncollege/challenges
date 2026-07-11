{
  pkgs,
  lib ? pkgs.lib,
  name,
  dataDir,
  runDir,
  workspaceSubnet,
}:

let
  unitName = component: "${name}-${component}";

  containerdDataDir = "${dataDir}/containerd";
  containerdRunDir = "${runDir}/containerd";
  containerdSockPath = "${containerdRunDir}/containerd.sock";
  cniDataDir = "${dataDir}/cni";
  workspaceBridge = "${name}0";

  kataConfig = import ./kata.nix { inherit pkgs; };
  seccompProfile = import ./seccomp.nix { inherit pkgs; };

  jsonFormat = pkgs.formats.json { };
  cniConfigFile = jsonFormat.generate "10-${name}.conflist" {
    cniVersion = "1.1.0";
    name = name;
    plugins = [
      {
        type = "bridge";
        bridge = workspaceBridge;
        isGateway = true;
        ipMasq = false;
        portIsolation = true;
        macspoofchk = true;
        ipam = {
          type = "host-local";
          dataDir = cniDataDir;
          ranges = [
            [ { subnet = workspaceSubnet; } ]
          ];
          routes = [ { dst = "0.0.0.0/0"; } ];
        };
      }
    ];
  };
  cniConfigDir = pkgs.linkFarm "${name}-cni" [
    {
      name = "10-${name}.conflist";
      path = cniConfigFile;
    }
  ];

  containerdConfig = pkgs.writeText "${name}-containerd-config.toml" ''
    version = 4
    root = "${containerdDataDir}"
    state = "${containerdRunDir}"
    disabled_plugins = ["io.containerd.nri.v1.nri"]

    [plugins."io.containerd.cri.v1.images".pinned_images]
      sandbox = "registry.k8s.io/pause:3.10.2"

    [plugins."io.containerd.cri.v1.runtime".containerd]
      default_runtime_name = "kata"

    [plugins."io.containerd.cri.v1.runtime".containerd.runtimes.kata]
      runtime_type = "io.containerd.kata.v2"

    [plugins."io.containerd.cri.v1.runtime".containerd.runtimes.kata.options]
      ConfigPath = "${kataConfig}"

    [plugins."io.containerd.cri.v1.runtime".cni]
      bin_dirs = ["${pkgs.cni-plugins}/bin"]
      conf_dir = "${cniConfigDir}"
      max_conf_num = 1
      use_internal_loopback = true

    [plugins."io.containerd.server.v1.grpc"]
      address = "${containerdSockPath}"

    [plugins."io.containerd.server.v1.ttrpc"]
      address = "${containerdSockPath}.ttrpc"
  '';
in
{
  inherit
    containerdDataDir
    containerdRunDir
    containerdSockPath
    seccompProfile
    workspaceBridge
    ;

  services = {
    "${unitName "containerd"}" = {
      description = "pwn.college workspace container runtime";
      after = [ "local-fs.target" ];
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        Type = "notify";
        ExecStart = "${pkgs.containerd}/bin/containerd --config ${containerdConfig}";
        Environment = "PATH=${lib.makeBinPath [ pkgs.kata-runtime pkgs.nftables pkgs.runc ]}";
        Restart = "on-failure";
        TimeoutStartSec = 60;
        NotifyAccess = "all";
        Delegate = true;
        KillMode = "process";
        LimitNPROC = "infinity";
        LimitCORE = "infinity";
        TasksMax = "infinity";
        OOMScoreAdjust = -500;
      };
    };
  };

  tmpfilesRules = [
    "d ${containerdRunDir} 0711 root root -"
    "d ${containerdDataDir} 0711 root root -"
    "d ${cniDataDir} 0711 root root -"
  ];
}
