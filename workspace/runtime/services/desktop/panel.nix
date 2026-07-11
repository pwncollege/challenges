{
  pkgs,
  lib ? pkgs.lib,
  packageLaunchers ? [ ],
}:
let
  launcherPlugin =
    id: desktopFile:
    lib.concatStringsSep "\n" [
      "    <property name=\"plugin-${toString id}\" type=\"string\" value=\"launcher\">"
      "      <property name=\"items\" type=\"array\">"
      "        <value type=\"string\" value=\"${desktopFile}\"/>"
      "      </property>"
      "    </property>"
    ];
  packageLauncherPluginIds = lib.genList (index: 100 + index) (builtins.length packageLaunchers);
  packageLauncherPlugins = lib.imap0 (
    index: desktopFile: launcherPlugin (100 + index) desktopFile
  ) packageLaunchers;
  packageLauncherPluginIdText = lib.concatMapStringsSep "\n" (
    id: "        <value type=\"int\" value=\"${toString id}\"/>"
  ) packageLauncherPluginIds;
  packageLauncherPluginText = lib.concatStringsSep "\n" packageLauncherPlugins;
in
pkgs.replaceVars ./etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml {
  packageLauncherPluginIds = packageLauncherPluginIdText;
  packageLauncherPlugins = packageLauncherPluginText;
}
