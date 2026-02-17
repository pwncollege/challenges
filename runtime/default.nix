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

  jsonFormat = pkgs.formats.json { };

  kataKernel = import ./kernel.nix { inherit pkgs name; };
  seccompProfile = import ./seccomp.nix { inherit pkgs name; };

  toSystemdUnit =
    unitFileName: sections:
    pkgs.writeText unitFileName (lib.generators.toINI { listsAsDuplicateKeys = true; } sections);

  systemdServiceCommon = {
    Service = {
      Type = "notify";
      Environment = "PATH=${pkgs.kata-runtime}/bin:${pkgs.docker}/bin:${pkgs.containerd}/bin:/usr/sbin:/usr/bin:/sbin:/bin";
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
    "containerd" = "${containerdSockPath}";

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

  dockerSystemdSocketUnit = toSystemdUnit "${name}-docker.socket" {
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

  dockerSystemdServiceUnit = toSystemdUnit "${name}-docker.service" (
    lib.recursiveUpdate systemdServiceCommon {
      Unit = {
        Description = "pwn.college challenge runtime docker daemon";
        Requires = [
          "${name}-docker.socket"
          "${name}-containerd.service"
        ];
        After = [
          "local-fs.target"
          "${name}-containerd.service"
        ];
      };
      Service = {
        ExecStart = "${pkgs.docker}/bin/dockerd --config-file=${dockerDaemonJson} -H fd://";
      };
    }
  );

  containerdConfigToml = pkgs.writeText "${name}-containerd-config.toml" ''
    version = 2
    root = "${containerdDataDir}"
    state = "${containerdRunDir}"

    [grpc]
      address = "${containerdSockPath}"
  '';

  containerdServiceUnit = toSystemdUnit "${name}-containerd.service" (
    lib.recursiveUpdate systemdServiceCommon {
      Unit = {
        Description = "pwn.college challenge runtime containerd";
        After = "local-fs.target";
      };
      Service = {
        ExecStart = "${pkgs.containerd}/bin/containerd --config ${containerdConfigToml}";
        NotifyAccess = "all";
        TimeoutStartSec = 60;
      };
    }
  );

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

    docker_host="unix://${dockerSockPath}"

    docker_socket_unit="${name}-docker.socket"
    docker_service_unit="${name}-docker.service"
    containerd_service_unit="${name}-containerd.service"

    current_service_link="$(readlink -f "/run/systemd/system/$docker_service_unit" 2>/dev/null || true)"

    if [[ "$current_service_link" == "${dockerSystemdServiceUnit}" ]] \
      && DOCKER_HOST="$docker_host" docker info >/dev/null 2>&1; then
      echo "$docker_host"
      exit 0
    fi

    install -d -m 0711 -o root -g root \
      ${dockerRunDir} ${dockerDataDir} ${containerdRunDir} ${containerdDataDir}

    mkdir -p /run/systemd/system
    ln -sfn "${dockerSystemdSocketUnit}" "/run/systemd/system/$docker_socket_unit"
    ln -sfn "${dockerSystemdServiceUnit}" "/run/systemd/system/$docker_service_unit"
    ln -sfn "${containerdServiceUnit}" "/run/systemd/system/$containerd_service_unit"

    mkdir -p /nix/var/nix/gcroots
    ln -sfn "${dockerSystemdServiceUnit}" "/nix/var/nix/gcroots/${name}"

    systemctl daemon-reload
    systemctl enable --runtime "$containerd_service_unit" >/dev/null 2>&1 || true
    if ! timeout 60 systemctl restart "$containerd_service_unit" >/dev/null; then
      echo "Error: failed to (re)start $containerd_service_unit" >&2
      systemctl status "$containerd_service_unit" --no-pager >&2 || true
      exit 1
    fi
    systemctl enable --runtime "$docker_socket_unit" >/dev/null 2>&1 || true
    if ! timeout 60 systemctl restart "$docker_socket_unit" >/dev/null 2>&1; then
      echo "Error: failed to (re)start $docker_socket_unit" >&2
      systemctl status "$docker_socket_unit" --no-pager >&2 || true
      exit 1
    fi
    if ! timeout 60 systemctl restart "$docker_service_unit" >/dev/null 2>&1; then
      echo "Error: failed to (re)start $docker_service_unit" >&2
      systemctl status "$docker_service_unit" --no-pager >&2 || true
      exit 1
    fi
    if ! timeout 60 env DOCKER_HOST="$docker_host" docker info >/dev/null 2>&1; then
      echo "Error: dockerd not reachable at $docker_host" >&2
      systemctl status "$docker_service_unit" --no-pager >&2 || true
      exit 1
    fi

    echo "$docker_host"
  '';
}
