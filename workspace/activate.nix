{
  pkgs,
  lib,
  workspaceRuntime,
}:

let
  platform = import ./platform {
    inherit
      pkgs
      lib
      workspaceRuntime
      ;
  };

  toSystemdUnit =
    unitFileName: sections:
    let
      unitDirectory = pkgs.writeTextDir unitFileName (
        lib.generators.toINI { listsAsDuplicateKeys = true; } sections
      );
    in
    "${unitDirectory}/${unitFileName}";

  renderService =
    unitName: service:
    toSystemdUnit "${unitName}.service" (
      {
        Unit = {
          Description = service.description;
        }
        // lib.optionalAttrs (service ? requires) { Requires = service.requires; }
        // lib.optionalAttrs (service ? after) { After = service.after; };
        Service = service.serviceConfig;
      }
      // lib.optionalAttrs (service ? wantedBy) {
        Install.WantedBy = service.wantedBy;
      }
    );

  renderSocket =
    unitName: socket:
    toSystemdUnit "${unitName}.socket" {
      Unit.Description = socket.description;
      Socket = socket.socketConfig;
      Install.WantedBy = socket.wantedBy;
    };

  serviceUnitFiles = lib.mapAttrs' (
    unitName: service: lib.nameValuePair "${unitName}.service" (renderService unitName service)
  ) platform.services;
  socketUnitFiles = lib.mapAttrs' (
    unitName: socket: lib.nameValuePair "${unitName}.socket" (renderSocket unitName socket)
  ) platform.sockets;
  unitFiles = serviceUnitFiles // socketUnitFiles;
  unitDirectory = pkgs.linkFarm "${platform.name}-units" (
    lib.mapAttrsToList (name: path: { inherit name path; }) unitFiles
  );
in
pkgs.writeShellApplication {
  name = platform.name;
  runtimeInputs = with pkgs; [
    bash
    coreutils
    curl
    docker
    systemd
  ];
  text = ''
    set -euo pipefail

    docker_host='unix://${platform.dockerSockPath}'

    unit_files=("${unitDirectory}"/*)
    unit_file_names=("''${unit_files[@]##*/}")
    current_systemd_units='${platform.runDir}/current-systemd-units'

    emit_environment() {
      printf 'export DOCKER_HOST=%q\n' "$docker_host"
      printf 'export PWN_WORKSPACE_DAEMON_URL=%q\n' '${platform.daemonURL}'
    }

    check_health() {
      curl --fail --silent '${platform.daemonURL}/api/health' >/dev/null 2>&1
    }

    wait_for_health() {
      local deadline=$((SECONDS + 60))
      until check_health; do
        if (( SECONDS >= deadline )); then
          return 1
        fi
        sleep 0.25
      done
    }

    install -d -m 0711 -o root -g root '${platform.runDir}'

    if [[ "$(readlink -f "$current_systemd_units" 2>/dev/null || true)" == '${unitDirectory}' ]] && check_health; then
      emit_environment
      exit 0
    fi

    install -d -m 0711 -o root -g root \
      '${platform.dockerRunDir}' \
      '${platform.dockerDataDir}' \
      '${platform.containerdRunDir}' \
      '${platform.containerdDataDir}'

    mkdir -p /nix/var/nix/gcroots
    ln -sfn "$0" '/nix/var/nix/gcroots/${platform.name}'

    systemctl enable --runtime --force --quiet "''${unit_files[@]}"
    if ! timeout 60 systemctl restart "''${unit_file_names[@]}" >/dev/null 2>&1; then
      echo 'Error: failed to (re)start workspace services' >&2
      systemctl status "''${unit_file_names[@]}" --no-pager >&2 || true
      exit 1
    fi
    if ! wait_for_health; then
      echo 'Error: workspace services failed health check' >&2
      systemctl status "''${unit_file_names[@]}" --no-pager >&2 || true
      exit 1
    fi

    ln -sfn '${unitDirectory}' "$current_systemd_units"
    emit_environment
  '';
}
