{
  description = "pwn.college challenges dev env";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs =
    { self, nixpkgs }:
    let
      lib = nixpkgs.lib;
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f: lib.genAttrs systems (system: f system);
    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };

          jsonFormat = pkgs.formats.json { };

          # Systemd unit "basename" (service/socket). Keep this stable; it becomes the unit file name.
          unitBase = "pwn-challenge-runtime";

          toSystemdUnit =
            name: sections:
            pkgs.writeText name (lib.generators.toINI { listsAsDuplicateKeys = true; } sections);

          kataConfigToml =
            pkgs.runCommand "${unitBase}-kata-config.toml" { } ''
              substitute ${pkgs.kata-runtime}/share/defaults/kata-containers/configuration.toml "$out" \
                --replace-fail \
                  'enable_annotations = ["enable_iommu", "virtio_fs_extra_args", "kernel_params"]' \
                  'enable_annotations = ["enable_iommu", "virtio_fs_extra_args", "kernel_params", "default_memory"]'
            '';

          dockerDaemonJson = jsonFormat.generate "${unitBase}-daemon.json" {
            "data-root" = "/var/lib/pwn.college/docker";
            "exec-root" = "/run/pwn.college/docker";
            "pidfile" = "/run/pwn.college/docker/dockerd.pid";
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

          systemdSocketUnit = toSystemdUnit "${unitBase}.socket" {
            Unit = {
              Description = "pwn.college docker socket";
            };
            Socket = {
              ListenStream = "/run/pwn.college/docker/docker.sock";
              SocketMode = "0666";
            };
            Install = {
              WantedBy = "sockets.target";
            };
          };

          systemdServiceUnit = toSystemdUnit "${unitBase}.service" {
            Unit = {
              Description = "pwn.college docker daemon";
              Requires = "${unitBase}.socket";
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

          pwnChallengeRuntime = pkgs.writeShellApplication {
            name = "pwn-challenge-runtime";
            runtimeInputs = with pkgs; [
              bash
              coreutils
              docker
              systemd
            ];
            text = ''
              set -euo pipefail

              unit_base="${unitBase}"
              socket_unit="$unit_base.socket"
              service_unit="$unit_base.service"
              host="unix:///run/pwn.college/docker/docker.sock"

              current_execstart="$(systemctl show -p ExecStart "$service_unit" 2>/dev/null || true)"
              want_cfg="--config-file=${dockerDaemonJson}"

              # Fast path: already reachable and already using the expected daemon config.
              if [[ "$current_execstart" == *"$want_cfg"* ]] && DOCKER_HOST="$host" docker info >/dev/null 2>&1; then
                echo "$host"
                exit 0
              fi

              echo "pwn-challenge-runtime: installing/starting dockerd..." >&2
              install -d -m 1777 -o root -g root /run/pwn.college/docker
              install -d -m 0711 -o root -g root /var/lib/pwn.college/docker

              # Register runtime units by linking Nix store unit files into systemd's runtime search path.
              mkdir -p /run/systemd/system
              ln -sfn "${systemdSocketUnit}" "/run/systemd/system/$socket_unit"
              ln -sfn "${systemdServiceUnit}" "/run/systemd/system/$service_unit"

              # GC root so the store paths referenced by the unit (dockerd/runtime/config) don't disappear.
              mkdir -p /nix/var/nix/gcroots
              ln -sfn "${systemdServiceUnit}" "/nix/var/nix/gcroots/$unit_base"

              systemctl daemon-reload
              systemctl enable --runtime --now "$socket_unit" >/dev/null 2>&1 || true
              systemctl try-restart "$service_unit" >/dev/null 2>&1 || true

              # Trigger socket activation and verify reachability (non-fatal: still print host).
              if ! DOCKER_HOST="$host" docker info >/dev/null 2>&1; then
                echo "pwn-challenge-runtime: WARNING: dockerd still not reachable at $host" >&2
              fi

              echo "$host"
            '';
          };
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              git
              jq
              docker
              kata-runtime
              pwnChallengeRuntime
            ];
            shellHook = ''
              export DOCKER_HOST="$(sudo ${pwnChallengeRuntime}/bin/pwn-challenge-runtime)"
            '';
          };
        });
    };
}
