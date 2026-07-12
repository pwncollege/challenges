{
  pkgs,
  name,
  dataDir,
  workspaceSubnet,
  egressAddress,
  egressDomains,
}:

let
  cniDataDir = "${dataDir}/cni";
  workspaceBridge = "${name}0";
  networkPolicy = import ./policy { inherit pkgs; };
  egress = import ./egress {
    inherit
      pkgs
      name
      workspaceSubnet
      ;
    address = egressAddress;
    domains = egressDomains;
  };

  jsonFormat = pkgs.formats.json { };
  cniConfigFile = jsonFormat.generate "10-${name}.conflist" {
    cniVersion = "1.1.0";
    name = name;
    plugins = [
      {
        type = "bridge";
        bridge = workspaceBridge;
        isGateway = true;
        ipMasq = false;
        portIsolation = true;
        ipam = {
          type = "host-local";
          dataDir = cniDataDir;
          ranges = [
            [ { subnet = workspaceSubnet; } ]
          ];
          routes = [ { dst = "0.0.0.0/0"; } ];
        };
      }
      {
        type = "pwn-network-policy";
        bridge = workspaceBridge;
        agentPort = 8000;
        inherit egressAddress;
      }
    ];
  };
  cniConfigDir = pkgs.linkFarm "${name}-cni" [
    {
      name = "10-${name}.conflist";
      path = cniConfigFile;
    }
  ];
in
{
  inherit
    cniConfigDir
    networkPolicy
    ;
  egressAddress = egress.address;
  egressPolicyServiceName = egress.policyServiceName;
  egressServiceName = egress.serviceName;
  services = egress.services;
  tmpfilesRules = [
    "d ${cniDataDir} 0711 root root -"
  ];
}
