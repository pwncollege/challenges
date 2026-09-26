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
      daemonListenAddress
      egressAddress
      egressDomains
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

    daemonListenAddress = lib.mkOption {
      type = lib.types.str;
      default = "127.0.0.1:8000";
      description = "Listen address for the workspace daemon HTTP API.";
    };

    egressAddress = lib.mkOption {
      type = lib.types.str;
      default = "192.0.2.1";
      description = "Synthetic IPv4 address used for whitelisted workspace DNS and HTTP traffic.";
    };

    egressDomains = lib.mkOption {
      type = lib.types.listOf lib.types.nonEmptyStr;
      default = [ "example.com" ];
      description = "Domain names allowed through workspace egress. A wildcard may replace the complete leftmost label; an empty list denies all domains.";
      example = [
        "example.com"
        "*.example.net"
      ];
    };

    workspaceSubnet = lib.mkOption {
      type = lib.types.str;
      default = "172.31.0.0/20";
      description = "IPv4 subnet allocated to workspaces on this node.";
    };

    volumeBasePath = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      description = "Optional directory for persistent ext4 home images.";
    };

  };

  config = lib.mkIf cfg.enable {
    systemd.services = platform.services;
    systemd.sockets = platform.sockets;
    systemd.tmpfiles.rules = platform.tmpfilesRules;
  };
}
