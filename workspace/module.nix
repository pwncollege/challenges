{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.services.pwn-workspace;
  platform = import ./platform {
    inherit pkgs lib;
    inherit (cfg)
      workspaceRuntime
      dataDir
      runDir
      daemonListenAddress
      workspaceNetwork
      workspaceSubnet
      volumeBasePath
      publicKey
      ;
  };
in
{
  options.services.pwn-workspace = {
    enable = lib.mkEnableOption "the pwn.college workspace runtime";

    workspaceRuntime = lib.mkOption {
      type = lib.types.package;
      description = "Nix workspace runtime made available inside Kata workspaces.";
    };

    publicKey = lib.mkOption {
      type = lib.types.nullOr (lib.types.strMatching "[0-9a-fA-F]{64}");
      default = null;
      description = "Optional hex-encoded raw Ed25519 control-plane public key used to authenticate API requests.";
    };

    dataDir = lib.mkOption {
      type = lib.types.str;
      default = "/var/lib/pwn.college";
      description = "Persistent state directory for the dedicated container runtime.";
    };

    runDir = lib.mkOption {
      type = lib.types.str;
      default = "/run/pwn.college";
      description = "Runtime state directory for sockets and process state.";
    };

    daemonListenAddress = lib.mkOption {
      type = lib.types.str;
      default = "127.0.0.1:8000";
      description = "Listen address for the workspace daemon HTTP API.";
    };

    workspaceNetwork = lib.mkOption {
      type = lib.types.str;
      default = "pwn-workspace";
      description = "Dedicated Docker network used by workspaces.";
    };

    workspaceSubnet = lib.mkOption {
      type = lib.types.str;
      default = "172.31.0.0/20";
      description = "IPv4 subnet used when provisioning the workspace network.";
    };

    volumeBasePath = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      description = "Optional Btrfs base path for persistent workspace volumes.";
    };

  };

  config = lib.mkIf cfg.enable {
    systemd.services = platform.services;
    systemd.sockets = platform.sockets;
    systemd.tmpfiles.rules = platform.tmpfilesRules;
  };
}
