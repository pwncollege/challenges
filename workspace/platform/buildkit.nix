{
  pkgs,
  lib ? pkgs.lib,
  name,
  dataDir,
  runDir,
  containerdSockPath,
}:

let
  unitName = component: "${name}-${component}";

  buildkitDataDir = "${dataDir}/buildkit";
  buildkitRunDir = "${runDir}/buildkit";
  buildkitSockPath = "${buildkitRunDir}/buildkitd.sock";

  buildkitConfig = pkgs.writeText "${name}-buildkit-config.toml" ''
    root = "${buildkitDataDir}"

    [grpc]
      address = ["unix://${buildkitSockPath}"]

    [worker.oci]
      enabled = false

    [worker.containerd]
      enabled = true
      address = "${containerdSockPath}"
      namespace = "k8s.io"
  '';
in
{
  inherit
    buildkitDataDir
    buildkitRunDir
    buildkitSockPath
    ;

  service = {
    description = "pwn.college workspace image builder";
    requires = [ "${unitName "containerd"}.service" ];
    after = [ "${unitName "containerd"}.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "notify";
      ExecStart = "${pkgs.buildkit}/bin/buildkitd --config ${buildkitConfig} --group users --containerd-worker-net bridge --containerd-cni-binary-dir ${pkgs.cni-plugins}/bin";
      Environment = "PATH=${
        lib.makeBinPath [
          pkgs.iptables
          pkgs.runc
        ]
      }";
      Restart = "on-failure";
      Delegate = true;
      KillMode = "process";
      RuntimeDirectory = "pwn.college/buildkit";
      RuntimeDirectoryMode = "0711";
      RuntimeDirectoryPreserve = "restart";
      StateDirectory = "pwn.college/buildkit";
      StateDirectoryMode = "0711";
    };
  };
}
