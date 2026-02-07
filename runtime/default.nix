{ pkgs, lib }:
let
  name = "pwn-challenge-runtime";

  dataRoot = "/var/lib/pwn.college/docker";
  runRoot = "/run/pwn.college/docker";
  sockPath = "${runRoot}/docker.sock";

  jsonFormat = pkgs.formats.json { };

  toSystemdUnit =
    unitFileName: sections:
    pkgs.writeText unitFileName (lib.generators.toINI { listsAsDuplicateKeys = true; } sections);

  kataConfigToml =
    pkgs.runCommand "${name}-kata-config.toml" { } ''
      substitute ${pkgs.kata-runtime}/share/defaults/kata-containers/configuration.toml "$out" \
        --replace-fail \
          'enable_annotations = ["enable_iommu", "virtio_fs_extra_args", "kernel_params"]' \
          'enable_annotations = ["enable_iommu", "virtio_fs_extra_args", "kernel_params", "default_memory"]'
    '';

  dockerDaemonJson = jsonFormat.generate "${name}-docker-daemon.json" {
    "data-root" = dataRoot;
    "exec-root" = runRoot;
    "pidfile" = "${runRoot}/dockerd.pid";
    "log-driver" = "journald";

    "features" = {
      "containerd-snapshotter" = true;
    };

    "runtimes" = {
      "kata" = {
        "runtimeType" = "io.containerd.kata.v2";
        "options" = {
          "ConfigPath" = "${kataConfigToml}";
        };
      };
    };
  };

  systemdSocketUnit = toSystemdUnit "${name}.socket" {
    Unit = {
      Description = "pwn.college challenge runtime docker socket";
    };
    Socket = {
      ListenStream = sockPath;
      SocketMode = "0666";
    };
    Install = {
      WantedBy = "sockets.target";
    };
  };

  systemdServiceUnit = toSystemdUnit "${name}.service" {
    Unit = {
      Description = "pwn.college challenge runtime docker daemon";
      Requires = "${name}.socket";
      After = "local-fs.target";
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

in
pkgs.writeShellApplication {
  inherit name;
  runtimeInputs = with pkgs; [
    bash
    coreutils
    docker
    systemd
  ];
  text = ''
    set -euo pipefail

    unit_base="${name}"
    socket_unit="$unit_base.socket"
    service_unit="$unit_base.service"
    host="unix://${sockPath}"

    current_execstart="$(systemctl show -p ExecStart "$service_unit" 2>/dev/null || true)"
    want_cfg="--config-file=${dockerDaemonJson}"

    if [[ "$current_execstart" == *"$want_cfg"* ]] && DOCKER_HOST="$host" docker info >/dev/null 2>&1; then
      echo "$host"
      exit 0
    fi

    install -d -m 0711 -o root -g root ${runRoot}
    install -d -m 0711 -o root -g root ${dataRoot}

    mkdir -p /run/systemd/system
    ln -sfn "${systemdSocketUnit}" "/run/systemd/system/$socket_unit"
    ln -sfn "${systemdServiceUnit}" "/run/systemd/system/$service_unit"

    mkdir -p /nix/var/nix/gcroots
    ln -sfn "${systemdServiceUnit}" "/nix/var/nix/gcroots/$unit_base"

    systemctl daemon-reload
    systemctl enable --runtime --now "$socket_unit" >/dev/null 2>&1 || true
    systemctl try-restart "$service_unit" >/dev/null 2>&1 || true

    if ! DOCKER_HOST="$host" docker info >/dev/null 2>&1; then
      echo "Error: dockerd not reachable at $host" >&2
      exit 1
    fi

    echo "$host"
  '';
}
