{
  pkgs,
  lib ? pkgs.lib,
  workspaceRuntime,
  publicKey ? null,
  dataDir ? "/var/lib/pwn.college",
  runDir ? "/run/pwn.college",
  daemonListenAddress ? "127.0.0.1:8000",
  workspaceNetwork ? "pwn-workspace",
  workspaceSubnet ? "172.31.0.0/20",
  volumeBasePath ? null,
}:

let
  name = "pwn-workspace";
  unitName = component: "${name}-${component}";

  container = import ./container {
    inherit
      pkgs
      lib
      name
      dataDir
      runDir
      workspaceNetwork
      workspaceSubnet
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
      workspaceNetwork
      publicKey
      volumeBasePath
      ;
    inherit (container) dockerSockPath;
    inherit (store) nixStorePath;
  };
in
{
  inherit
    name
    dataDir
    runDir
    daemonListenAddress
    workspaceNetwork
    workspaceSubnet
    ;
  daemonURL = daemon.url;
  inherit (container)
    dockerDataDir
    dockerRunDir
    dockerSockPath
    containerdDataDir
    containerdRunDir
    containerdSockPath
    sockets
    ;

  services = container.services // {
    "${unitName "store"}" = store.service;
    "${unitName "daemon"}" = daemon.service;
  };

  tmpfilesRules = [
    "d ${runDir} 0711 root root -"
  ]
  ++ store.tmpfilesRules
  ++ container.tmpfilesRules;
}
