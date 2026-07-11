{
  pkgs,
  packageLaunchers ? [ ],
}:
let
  lib = pkgs.lib;
  desktopIcons = import ./icons.nix { inherit pkgs lib; };
  panelConfig = import ./panel.nix { inherit pkgs lib packageLaunchers; };

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
      adwaita-fonts
      adwaita-icon-theme
      dbus
      dejavu_fonts
      elementary-xfce-icon-theme
      fontconfig
      garcon
      gnome-themes-extra
      hack-font
      hicolor-icon-theme
      shared-mime-info
      desktopIcons
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
    postBuild = ''
      while IFS= read -r source; do
        target="$out/etc/''${source#${./etc}/}"
        rm -f "$target"
        install -Dm0644 "$source" "$target"
      done < <(find ${./etc} -type f)
      install -Dm0644 ${panelConfig} "$out/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml"

      while IFS= read -r source; do
        target="$out/share/''${source#${./share}/}"
        rm -f "$target"
        install -Dm0644 "$source" "$target"
      done < <(find ${./share} -type f)

      install -Dm0644 ${pkgs.xfce4-terminal}/share/applications/xfce4-terminal.desktop "$out/share/applications/xfce4-terminal.desktop"
      substituteInPlace "$out/share/applications/xfce4-terminal.desktop" \
        --replace-fail "Icon=org.xfce.terminal" "Icon=${pkgs.xfce4-terminal}/share/icons/hicolor/16x16/apps/org.xfce.terminal.png"
    '';
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
      export FONTCONFIG_FILE="${pkgs.fontconfig.out}/etc/fonts/fonts.conf"
      export FONTCONFIG_PATH="${pkgs.fontconfig.out}/etc/fonts"
      export XDG_DATA_DIRS="/run/workspace/profile/share:${desktopEnv}/share:''${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
      export XDG_CONFIG_HOME=/run/workspace/user/config
      export XDG_CONFIG_DIRS="${desktopEnv}/etc/xdg:''${XDG_CONFIG_DIRS:-/etc/xdg}"

      runtime_dir=/run/workspace/user/services/desktop
      mkdir -p "$runtime_dir"
      rm -f "$runtime_dir/novnc.sock" "$runtime_dir/Xvnc.sock"

      xfconf_dir="$XDG_CONFIG_HOME/xfce4/xfconf/xfce-perchannel-xml"
      mkdir -p "$xfconf_dir"
      cp -f ${desktopEnv}/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/*.xml "$xfconf_dir/"
      chmod u+w "$xfconf_dir"/*.xml

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

      dbus-run-session \
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

    while IFS= read -r source; do
      target="$out/share/''${source#${./share}/}"
      rm -f "$target"
      install -Dm0644 "$source" "$target"
    done < <(find ${./share} -type f)
  '';
}
