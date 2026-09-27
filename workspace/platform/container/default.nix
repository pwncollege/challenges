{
  pkgs,
  lib ? pkgs.lib,
  name,
  dataDir,
  runDir,
  cniConfigDir,
  networkPolicy,
  egressPolicyServiceName,
}:

let
  unitName = component: "${name}-${component}";

  containerdDataDir = "${dataDir}/containerd";
  containerdRunDir = "${runDir}/containerd";
  containerdSockPath = "${containerdRunDir}/containerd.sock";

  kata = import ./kata.nix { inherit pkgs; };
  package = pkgs.containerd.overrideAttrs (old: {
    patches = (old.patches or [ ]) ++ [ ./containerd-sparse.patch ];
    doCheck = true;
    checkPhase = ''
      runHook preCheck
      go test ./plugins/snapshots/blockfile -run TestCopyFileWithSyncPreservesHoles -v
      runHook postCheck
    '';
  });
  seccompProfile = import ./seccomp.nix { inherit pkgs; };

  scratch = "${containerdDataDir}/empty-8GiB.ext4";
  prepareScratch = pkgs.writeShellScript "${name}-containerd-scratch" ''
    set -euo pipefail
    if [[ ! -e '${scratch}' ]]; then
      ${pkgs.coreutils}/bin/truncate -s 8G '${scratch}.tmp'
      ${pkgs.e2fsprogs}/bin/mkfs.ext4 -q -F -m 0 -b 4096 \
        -E lazy_itable_init=0,lazy_journal_init=0 '${scratch}.tmp'
      ${pkgs.coreutils}/bin/mv '${scratch}.tmp' '${scratch}'
    fi
  '';

  containerdConfig = pkgs.writeText "${name}-containerd-config.toml" ''
    version = 4
    root = "${containerdDataDir}"
    state = "${containerdRunDir}"
    disabled_plugins = ["io.containerd.nri.v1.nri"]

    [plugins."io.containerd.cri.v1.images"]
      snapshotter = "blockfile"

    [plugins."io.containerd.cri.v1.images".pinned_images]
      sandbox = "registry.k8s.io/pause:3.10.2"

    [plugins."io.containerd.cri.v1.runtime".containerd]
      default_runtime_name = "kata"

    [plugins."io.containerd.cri.v1.runtime".containerd.runtimes.kata]
      runtime_type = "io.containerd.kata.v2"

    [plugins."io.containerd.cri.v1.runtime".containerd.runtimes.kata.options]
      ConfigPath = "${kata.config}"

    [plugins."io.containerd.snapshotter.v1.blockfile"]
      scratch_file = "${scratch}"
      root_path = "${containerdDataDir}/blockfile"
      fs_type = "ext4"

    [[plugins."io.containerd.transfer.v1.local".unpack_config]]
      platform = "linux/amd64"
      snapshotter = "blockfile"

    [plugins."io.containerd.cri.v1.runtime".cni]
      bin_dirs = ["${networkPolicy}/bin", "${pkgs.cni-plugins}/bin"]
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
    ;

  services = {
    "${unitName "containerd"}" = {
      description = "pwn.college workspace container runtime";
      requires = [ "${egressPolicyServiceName}.service" ];
      after = [
        "${egressPolicyServiceName}.service"
        "local-fs.target"
      ];
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        Type = "notify";
        ExecStartPre = prepareScratch;
        ExecStart = "${package}/bin/containerd --config ${containerdConfig}";
        Environment = "PATH=${
          lib.makeBinPath [
            kata.package
            pkgs.runc
          ]
        }";
        Restart = "on-failure";
        TimeoutStartSec = 60;
        NotifyAccess = "all";
        Delegate = true;
        KillMode = "process";
        LimitNPROC = "infinity";
        LimitCORE = "infinity";
        TasksMax = "infinity";
        OOMScoreAdjust = -500;
        RuntimeDirectory = "pwn.college/containerd";
        RuntimeDirectoryMode = "0711";
        RuntimeDirectoryPreserve = "restart";
        StateDirectory = "pwn.college/containerd";
        StateDirectoryMode = "0711";
      };
    };
  };
}
