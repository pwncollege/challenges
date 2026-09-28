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
    patches = (old.patches or [ ]) ++ [ ./containerd-erofs.patch ];
    nativeCheckInputs = (old.nativeCheckInputs or [ ]) ++ [ pkgs.erofs-utils ];
    doCheck = true;
    checkPhase = ''
      runHook preCheck
      go test ./plugins/mount/fsview/erofs -v
      runHook postCheck
    '';
  });
  seccompProfile = import ./seccomp.nix { inherit pkgs; };

  containerdConfig = pkgs.writeText "${name}-containerd-config.toml" ''
    version = 4
    root = "${containerdDataDir}"
    state = "${containerdRunDir}"
    disabled_plugins = ["io.containerd.nri.v1.nri"]

    [plugins."io.containerd.cri.v1.images"]
      snapshotter = "erofs"
      use_local_image_pull = true
      discard_unpacked_layers = true

    [plugins."io.containerd.cri.v1.images".pinned_images]
      sandbox = "registry.k8s.io/pause:3.10.2"

    [plugins."io.containerd.cri.v1.runtime".containerd]
      default_runtime_name = "kata"

    [plugins."io.containerd.cri.v1.runtime".containerd.runtimes.kata]
      runtime_type = "io.containerd.kata.v2"

    [plugins."io.containerd.cri.v1.runtime".containerd.runtimes.kata.options]
      ConfigPath = "${kata.config}"

    [plugins."io.containerd.snapshotter.v1.erofs"]
      # Kata supplies a bounded guest tmpfs for the writable upper.
      default_size = "0"

    [plugins."io.containerd.differ.v1.erofs"]
      # Bound compression CPU per layer while other workspaces start and run.
      mkfs_options = ["-T0", "--mkfs-time", "--sort=none", "-zlz4hc", "--workers=2"]
      enable_tar_index = false

    [plugins."io.containerd.service.v1.diff-service"]
      default = ["erofs", "walking"]

    [[plugins."io.containerd.transfer.v1.local".unpack_config]]
      platform = "linux/amd64"
      snapshotter = "erofs"
      differ = "erofs"

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
        ExecStartPre = "${pkgs.kmod}/bin/modprobe erofs";
        ExecStart = "${package}/bin/containerd --config ${containerdConfig}";
        Environment = "PATH=${
          lib.makeBinPath [
            kata.package
            pkgs.runc
            pkgs.erofs-utils
            pkgs.e2fsprogs
            pkgs.util-linux
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
