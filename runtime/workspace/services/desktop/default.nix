{ pkgs }:
let
  desktopWeb = pkgs.runCommand "workspace-desktop-web" { } ''
    mkdir -p $out/share/workspace/desktop
    cp -R ${pkgs.novnc}/share/webapps/novnc/. $out/share/workspace/desktop/
    cat > $out/share/workspace/desktop/index.html <<'EOF'
    <!doctype html>
    <meta http-equiv="refresh" content="0; url=vnc.html?autoconnect=1&resize=remote">
    <script>location.replace("vnc.html?autoconnect=1&resize=remote");</script>
    EOF
  '';

  desktopEnv = pkgs.symlinkJoin {
    name = "workspace-desktop-env";
    paths = with pkgs; [
      dbus
      dejavu_fonts
      elementary-xfce-icon-theme
      thunar
      xfce4-appfinder
      xfce4-exo
      xfce4-panel
      xfce4-session
      xfce4-settings
      xfce4-terminal
      xfconf
      xfdesktop
      xfwm4
    ];
  };

  desktopService = pkgs.writeShellApplication {
    name = "workspace-desktop";
    runtimeInputs = with pkgs; [
      bash
      curl
      dbus
      novnc
      python3Packages.websockify
      tigervnc
      desktopEnv
    ];
    text = ''
      export DISPLAY=:0
      export XDG_DATA_DIRS="${desktopEnv}/share:''${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
      export XDG_CONFIG_DIRS="${desktopEnv}/etc/xdg:''${XDG_CONFIG_DIRS:-/etc/xdg}"

      runtime_dir=/run/workspace/user/services/desktop
      mkdir -p "$runtime_dir"
      rm -f "$runtime_dir/novnc.sock" "$runtime_dir/Xvnc.sock"

      pids=()
      cleanup() {
        for pid in "''${pids[@]}"; do
          kill "$pid" 2>/dev/null || true
        done
        wait 2>/dev/null || true
      }
      trap cleanup EXIT INT TERM

      Xvnc "$DISPLAY" \
        -localhost 1 \
        -rfbunixpath "$runtime_dir/Xvnc.sock" \
        -SecurityTypes None \
        -nolisten tcp \
        -geometry 1024x768 \
        -depth 24 &
      pids+=("$!")

      until [ -e /tmp/.X11-unix/X0 ]; do sleep 0.1; done

      websockify \
        --web ${desktopWeb}/share/workspace/desktop \
        --unix-listen="$runtime_dir/novnc.sock" \
        --unix-listen-mode=0600 \
        --unix-target="$runtime_dir/Xvnc.sock" \
        &
      pids+=("$!")

      until curl -fs --unix-socket "$runtime_dir/novnc.sock" http://localhost/ >/dev/null; do sleep 0.1; done

      dbus-launch \
        --sh-syntax \
        --exit-with-session \
        --config-file=${pkgs.dbus}/share/dbus-1/session.conf \
        xfce4-session &
      pids+=("$!")

      wait -n "''${pids[@]}"
    '';
  };

  serviceConfig = pkgs.writeText "desktop.toml" ''
    name = "desktop"
    socket_path = "/run/workspace/user/services/desktop/novnc.sock"
    start_timeout = "30s"
    ready_path = "/"

    command = [
      "workspace-desktop",
    ]
  '';
in
pkgs.symlinkJoin {
  name = "workspace-desktop";
  paths = [
    desktopService
  ];
  postBuild = ''
    mkdir -p $out/share/workspace/services
    cp ${serviceConfig} $out/share/workspace/services/desktop.toml
  '';
}
