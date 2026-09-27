{
  pkgs,
  lib ? pkgs.lib,
  workspaceRuntime,
  publicKey ? null,
  daemonListenAddress ? "127.0.0.1:8000",
  egressAddress ? "192.0.2.1",
  egressDomains ? [ "example.com" ],
  workspaceSubnet ? "172.31.0.0/20",
  volumeBasePath ? null,
}:

let
  name = "pwn-workspace";
  dataDir = "/var/lib/pwn.college";
  runDir = "/run/pwn.college";
  unitName = component: "${name}-${component}";

  network = import ./network {
    inherit
      pkgs
      name
      dataDir
      egressAddress
      egressDomains
      workspaceSubnet
      ;
  };
  containerd = import ./container {
    inherit
      pkgs
      lib
      name
      dataDir
      runDir
      ;
    inherit (network)
      cniConfigDir
      networkPolicy
      egressPolicyServiceName
      ;
  };
  buildkit = import ./buildkit.nix {
    inherit
      pkgs
      lib
      name
      dataDir
      runDir
      ;
    inherit (containerd) containerdSockPath;
  };
  nixStoreImage = import ./store.nix { inherit pkgs workspaceRuntime; };
  daemon = import ./daemon {
    inherit
      pkgs
      lib
      name
      workspaceRuntime
      daemonListenAddress
      dataDir
      publicKey
      volumeBasePath
      nixStoreImage
      ;
    egressAddress = network.egressAddress;
    egressServiceName = network.egressServiceName;
    inherit (containerd) containerdSockPath seccompProfile;
  };
in
{
  inherit
    name
    dataDir
    runDir
    daemonListenAddress
    egressAddress
    egressDomains
    workspaceSubnet
    ;
  daemonURL = daemon.url;
  buildkitURL = "unix://${buildkit.buildkitSockPath}";
  inherit (buildkit)
    buildkitDataDir
    buildkitRunDir
    buildkitSockPath
    ;
  inherit (containerd)
    containerdDataDir
    containerdRunDir
    containerdSockPath
    ;

  sockets = { };

  services =
    network.services
    // containerd.services
    // {
      "${unitName "buildkit"}" = buildkit.service;
      "${unitName "daemon"}" = daemon.service;
    };

  tmpfilesRules = network.tmpfilesRules;
}
