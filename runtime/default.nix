{ pkgs, lib }:
let
  name = "pwn-challenge-runtime";

  dataRoot = "/var/lib/pwn.college/docker";
  runRoot = "/run/pwn.college/docker";
  sockPath = "${runRoot}/docker.sock";

  jsonFormat = pkgs.formats.json { };

  kataKernel = import ./kernel.nix { inherit pkgs name; };

  seccompBaseProfile = pkgs.fetchurl {
    # Pin the upstream Docker seccomp base profile so nix builds stay reproducible.
    url = "https://raw.githubusercontent.com/moby/profiles/9fb516320ad275f544b4995f424dfa8b6261cffa/seccomp/default.json";
    hash = "sha256-AVNvHR35OK5hHrog1jSeDeepm27N7hVJQnoLAbgwHig=";
  };

  seccompProfileScript = pkgs.writeText "${name}-seccomp.py" ''
    import json
    import sys

    READ_IMPLIES_EXEC = 0x0400000
    ADDR_NO_RANDOMIZE = 0x0040000

    with open(sys.argv[1]) as profile_file:
        seccomp = json.load(profile_file)

    existing_personality_values = []
    for syscalls in seccomp["syscalls"]:
        if "personality" not in syscalls["names"]:
            continue
        if syscalls["action"] != "SCMP_ACT_ALLOW":
            continue
        assert len(syscalls["args"]) == 1
        arg = syscalls["args"][0]
        assert list(arg.keys()) == ["index", "value", "op"]
        assert arg["index"] == 0, arg
        assert arg["op"] == "SCMP_CMP_EQ"
        existing_personality_values.append(arg["value"])

    new_personality_values = []
    for new_flag in [READ_IMPLIES_EXEC, ADDR_NO_RANDOMIZE]:
        for value in [0, *existing_personality_values]:
            new_value = value | new_flag
            if new_value not in existing_personality_values:
                new_personality_values.append(new_value)
                existing_personality_values.append(new_value)

    for new_value in new_personality_values:
        seccomp["syscalls"].append(
            {
                "names": ["personality"],
                "action": "SCMP_ACT_ALLOW",
                "args": [{"index": 0, "value": new_value, "op": "SCMP_CMP_EQ"}],
            }
        )

    with open(sys.argv[2], "w") as out_file:
        json.dump(seccomp, out_file)
  '';

  seccompProfile = pkgs.runCommand "${name}-seccomp.json" { nativeBuildInputs = [ pkgs.python3 ]; } ''
    python ${seccompProfileScript} ${seccompBaseProfile} "$out"
  '';

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
    "data-root" = dataRoot;
    "exec-root" = runRoot;
    "pidfile" = "${runRoot}/dockerd.pid";
    "log-driver" = "journald";
    "seccomp-profile" = "${seccompProfile}";

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
