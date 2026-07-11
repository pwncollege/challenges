{ pkgs }:
let
  codeService = pkgs.writeShellApplication {
    name = "workspace-code";
    runtimeInputs = [
      pkgs.code-server
    ];
    text = ''
      socket_path=/run/workspace/user/services/code/code-server.sock
      rm -f "$socket_path"

      exec code-server \
        --auth=none \
        --socket="$socket_path" \
        --socket-mode=0600 \
        --trusted-origins='*' \
        --disable-telemetry \
        --disable-update-check \
        --disable-workspace-trust \
        --config=/dev/null \
        "$HOME"
    '';
  };

  serviceConfig = pkgs.writeText "code.toml" ''
    name = "code"
    socket_path = "/run/workspace/user/services/code/code-server.sock"
    start_timeout = "30s"
    ready_path = "/"

    command = [
      "workspace-code",
    ]
  '';
in
pkgs.symlinkJoin {
  name = "workspace-code";
  paths = [
    codeService
  ];
  postBuild = ''
    mkdir -p $out/share/workspace/services
    cp ${serviceConfig} $out/share/workspace/services/code.toml
  '';
}
