{
  pkgs,
  lib ? pkgs.lib,
}:
let
  elementaryIconAliases = {
    "applications-accessories" = "categories/16/applications-accessories.png";
    "applications-development" = "categories/16/applications-development.png";
    "applications-internet" = "categories/16/applications-internet.png";
    "applications-other" = "places/16/start-here.png";
    "applications-science" = "categories/16/applications-science.png";
    "applications-system" = "apps/16/utilities-system-monitor.png";
    "org.xfce.appfinder" = "apps/16/org.xfce.appfinder.png";
    "org.xfce.filemanager" = "apps/16/system-file-manager.png";
    "org.xfce.mailreader" = "apps/16/internet-mail.png";
    "org.xfce.terminalemulator" = "apps/16/utilities-terminal.png";
    "org.xfce.webbrowser" = "apps/16/web-browser.png";
    "preferences-desktop" = "categories/16/preferences-desktop.png";
    "start-here" = "places/16/start-here.png";
  };
  hicolorAppIconAliases = [
    {
      package = pkgs.xfce4-terminal;
      names = [ "org.xfce.terminal" ];
    }
    {
      package = pkgs.xfce4-settings;
      names = [
        "org.xfce.settings.accessibility"
        "org.xfce.settings.appearance"
        "org.xfce.settings.color"
        "org.xfce.settings.default-applications"
        "org.xfce.settings.display"
        "org.xfce.settings.editor"
        "org.xfce.settings.keyboard"
        "org.xfce.settings.manager"
        "org.xfce.settings.mouse"
      ];
    }
    {
      package = pkgs.thunar;
      names = [ "org.xfce.thunar" ];
    }
    {
      package = pkgs.xfdesktop;
      names = [ "org.xfce.xfdesktop" ];
    }
    {
      package = pkgs.xfwm4;
      names = [
        "org.xfce.workspaces"
        "org.xfce.xfwm4"
        "org.xfce.xfwm4-tweaks"
      ];
    }
  ];
  elementaryAlias = name: source: {
    name = "share/pixmaps/${name}";
    path = "${pkgs.elementary-xfce-icon-theme}/share/icons/elementary-xfce/${source}";
  };
  hicolorAppAlias = package: name: {
    name = "share/pixmaps/${name}";
    path = "${package}/share/icons/hicolor/16x16/apps/${name}.png";
  };
  elementaryAliases = lib.mapAttrsToList elementaryAlias elementaryIconAliases;
  hicolorAliases = lib.concatMap (
    { package, names }:
    map (hicolorAppAlias package) names
  ) hicolorAppIconAliases;
in
pkgs.linkFarm "workspace-desktop-icons" (
  elementaryAliases
  ++ hicolorAliases
  ++ [
    {
      name = "share/pixmaps/pwncollege-applications";
      path = ./share/pixmaps/pwncollege-applications.png;
    }
  ]
)
