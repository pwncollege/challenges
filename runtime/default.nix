{ pkgs, lib }:
let
  name = "pwn-challenge-runtime";

  dataDir = "/var/lib/pwn.college";
  runDir = "/run/pwn.college";

  dockerDataDir = "${dataDir}/docker";
  dockerRunDir = "${runDir}/docker";
  dockerSockPath = "${dockerRunDir}/docker.sock";

  containerdDataDir = "${dataDir}/containerd";
  containerdRunDir = "${runDir}/containerd";
  containerdSockPath = "${containerdRunDir}/containerd.sock";
  containerdSockAddr = "unix://${containerdSockPath}";

  jsonFormat = pkgs.formats.json { };

  kataKernel = import ./kernel.nix { inherit pkgs name; };
  seccompProfile = import ./seccomp.nix { inherit pkgs name; };

  toSystemdUnit =
    unitFileName: sections:
    pkgs.writeText unitFileName (lib.generators.toINI { listsAsDuplicateKeys = true; } sections);

  kataConfigToml =
    pkgs.runCommand "${name}-kata-config.toml" { nativeBuildInputs = [ pkgs.gawk ]; }
      ''
        kernel_line="$(awk '$1 == "kernel" { print; exit }' ${pkgs.kata-runtime}/share/defaults/kata-containers/configuration.toml)"
        substitute ${pkgs.kata-runtime}/share/defaults/kata-containers/configuration.toml "$out" \
          --replace-fail \
            "$kernel_line" \
            'kernel = "${kataKernel}/share/kata-containers/vmlinux.container"' \
          --replace-fail \
            'enable_annotations = ["enable_iommu", "virtio_fs_extra_args", "kernel_params"]' \
            'enable_annotations = ["enable_iommu", "virtio_fs_extra_args", "kernel_params", "default_memory"]'
      '';

  dockerDaemonJson = jsonFormat.generate "${name}-docker-daemon.json" {
    "data-root" = dockerDataDir;
    "exec-root" = dockerRunDir;
    "pidfile" = "${dockerRunDir}/dockerd.pid";
    "log-driver" = "journald";
    "seccomp-profile" = "${seccompProfile}";
    "containerd" = containerdSockAddr;

    "features" = {
      "containerd-snapshotter" = true;
    };

    "runtimes" = {
      "kata" = {
        "runtimeType" = "${pkgs.kata-runtime}/bin/containerd-shim-kata-v2";
        "options" = {
          "ConfigPath" = "${kataConfigToml}";
        };
      };
    };
  };

  # Run a dedicated containerd so its content store (blobs/sha256/...) lives under /var/lib/pwn.college,
  # rather than the host's /var/lib/containerd.
  containerdConfigToml = pkgs.writeText "${name}-containerd-config.toml" ''
    version = 2
    root = "${containerdDataDir}"
    state = "${containerdRunDir}"

    [grpc]
      address = "${containerdSockPath}"
  '';

  dockerSystemdSocketUnit = toSystemdUnit "${name}.socket" {
    Unit = {
      Description = "pwn.college challenge runtime docker socket";
    };
    Socket = {
      ListenStream = dockerSockPath;
      SocketMode = "0666";
    };
    Install = {
      WantedBy = "sockets.target";
    };
  };

  dockerSystemdServiceUnit = toSystemdUnit "${name}.service" {
    Unit = {
      Description = "pwn.college challenge runtime docker daemon";
      Requires = [ "${name}.socket" "${name}-containerd.service" ];
      After = [ "local-fs.target" "${name}-containerd.service" ];
    };
    Service = {
      Type = "notify";
      ExecStart = "${pkgs.docker}/bin/dockerd --config-file=${dockerDaemonJson} -H fd://";
      Environment = "PATH=${pkgs.kata-runtime}/bin:${pkgs.docker}/bin:/usr/sbin:/usr/bin:/sbin:/bin";
      Restart = "on-failure";
      TimeoutStartSec = 0;
      Delegate = "yes";
      KillMode = "process";
      LimitNPROC = "infinity";
      LimitCORE = "infinity";
      TasksMax = "infinity";
      OOMScoreAdjust = -500;
    };
    Install = {
      WantedBy = "multi-user.target";
    };
  };

  containerdServiceUnit = toSystemdUnit "${name}-containerd.service" {
    Unit = {
      Description = "pwn.college challenge runtime containerd";
      After = "local-fs.target";
    };
    Service = {
      Type = "simple";
      ExecStart = "${pkgs.containerd}/bin/containerd --config ${containerdConfigToml}";
      Environment = "PATH=${pkgs.kata-runtime}/bin:${pkgs.containerd}/bin:/usr/sbin:/usr/bin:/sbin:/bin";
      Restart = "on-failure";
      TimeoutStartSec = 0;
      Delegate = "yes";
      KillMode = "process";
      LimitNPROC = "infinity";
      LimitCORE = "infinity";
      TasksMax = "infinity";
      OOMScoreAdjust = -500;
    };
    Install = {
      WantedBy = "multi-user.target";
    };
  };

in
pkgs.writeShellApplication {
  inherit name;
  runtimeInputs = with pkgs; [
    bash
    coreutils
    containerd
    docker
    systemd
  ];
  text = ''
    set -euo pipefail

    unit_base="${name}"
    socket_unit="$unit_base.socket"
    service_unit="$unit_base.service"
    containerd_unit="$unit_base-containerd.service"
    host="unix://${dockerSockPath}"

    current_execstart="$(systemctl show -p ExecStart "$service_unit" 2>/dev/null || true)"
    want_cfg="--config-file=${dockerDaemonJson}"

    if [[ "$current_execstart" == *"$want_cfg"* ]] && DOCKER_HOST="$host" docker info >/dev/null 2>&1; then
      echo "$host"
      exit 0
    fi

    install -d -m 0711 -o root -g root ${dockerRunDir}
    install -d -m 0711 -o root -g root ${dockerDataDir}
    install -d -m 0711 -o root -g root ${containerdRunDir}
    install -d -m 0711 -o root -g root ${containerdDataDir}

    mkdir -p /run/systemd/system
    ln -sfn "${dockerSystemdSocketUnit}" "/run/systemd/system/$socket_unit"
    ln -sfn "${dockerSystemdServiceUnit}" "/run/systemd/system/$service_unit"
    ln -sfn "${containerdServiceUnit}" "/run/systemd/system/$containerd_unit"

    mkdir -p /nix/var/nix/gcroots
    ln -sfn "${dockerSystemdServiceUnit}" "/nix/var/nix/gcroots/$unit_base"

    systemctl daemon-reload
    systemctl enable --runtime --now "$containerd_unit" >/dev/null 2>&1 || true
    systemctl enable --runtime --now "$socket_unit" >/dev/null 2>&1 || true
    systemctl try-restart "$service_unit" >/dev/null 2>&1 || true

    if ! DOCKER_HOST="$host" docker info >/dev/null 2>&1; then
      echo "Error: dockerd not reachable at $host" >&2
      exit 1
    fi

    echo "$host"
  '';
}
