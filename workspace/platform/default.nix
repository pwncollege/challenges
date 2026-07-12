{
  pkgs,
  lib ? pkgs.lib,
  workspaceRuntime,
  publicKey ? null,
  dataDir ? "/var/lib/pwn.college",
  runDir ? "/run/pwn.college",
  daemonListenAddress ? "127.0.0.1:8000",
  egressAddress ? "192.0.2.1",
  egressDomains ? [ "example.com" ],
  workspaceSubnet ? "172.31.0.0/20",
  volumeBasePath ? null,
}:

let
  name = "pwn-workspace";
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
  container = import ./container {
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
  store = import ./store.nix {
    inherit
      pkgs
      name
      workspaceRuntime
      dataDir
      ;
  };
  daemon = import ./daemon {
    inherit
      pkgs
      lib
      name
      workspaceRuntime
      daemonListenAddress
      runDir
      publicKey
      volumeBasePath
      ;
    egressAddress = network.egressAddress;
    egressServiceName = network.egressServiceName;
    inherit (container) containerdSockPath seccompProfile;
    inherit (store) nixStorePath;
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
  inherit (container)
    containerdDataDir
    containerdRunDir
    containerdSockPath
    ;

  sockets = { };

  services = network.services // container.services // {
    "${unitName "store"}" = store.service;
    "${unitName "daemon"}" = daemon.service;
  };

  tmpfilesRules = [
    "d ${runDir} 0711 root root -"
  ]
  ++ store.tmpfilesRules
  ++ network.tmpfilesRules
  ++ container.tmpfilesRules;
}
