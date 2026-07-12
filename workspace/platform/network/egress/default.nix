{
  pkgs,
  name,
  address,
  domains,
  workspaceSubnet,
}:

let
  unitName = component: "${name}-${component}";
  policyServiceName = unitName "egress-policy";
  serviceName = unitName "egress";
  egressInterface = "pwn-egress0";
  workspaceBridge = "${name}0";
  package = import ./package.nix { inherit pkgs; };
  domainsFile = pkgs.writeText "${name}-egress-domains.json" (builtins.toJSON domains);
  startPolicy = pkgs.writeShellScript "${name}-egress-policy-start" ''
    set -euo pipefail

    iptables='${pkgs.iptables}/bin/iptables'
    ip='${pkgs.iproute2}/bin/ip'

    "$ip" link delete '${egressInterface}' 2>/dev/null || true
    "$ip" link add '${egressInterface}' type dummy
    "$ip" address replace '${address}/32' dev '${egressInterface}'
    "$ip" link set '${egressInterface}' up

    "$iptables" --wait --check INPUT --in-interface '${workspaceBridge}' --source '${workspaceSubnet}' --destination '${address}' --protocol udp --dport 53 --jump ACCEPT 2>/dev/null \
      || "$iptables" --wait --insert INPUT 1 --in-interface '${workspaceBridge}' --source '${workspaceSubnet}' --destination '${address}' --protocol udp --dport 53 --jump ACCEPT
    "$iptables" --wait --check INPUT --in-interface '${workspaceBridge}' --source '${workspaceSubnet}' --destination '${address}' --protocol tcp --match multiport --dports 53,80,443 --jump ACCEPT 2>/dev/null \
      || "$iptables" --wait --insert INPUT 1 --in-interface '${workspaceBridge}' --source '${workspaceSubnet}' --destination '${address}' --protocol tcp --match multiport --dports 53,80,443 --jump ACCEPT
  '';
  stopPolicy = pkgs.writeShellScript "${name}-egress-policy-stop" ''
    set -euo pipefail

    iptables='${pkgs.iptables}/bin/iptables'
    while "$iptables" --wait --check INPUT --in-interface '${workspaceBridge}' --source '${workspaceSubnet}' --destination '${address}' --protocol udp --dport 53 --jump ACCEPT 2>/dev/null; do
      "$iptables" --wait --delete INPUT --in-interface '${workspaceBridge}' --source '${workspaceSubnet}' --destination '${address}' --protocol udp --dport 53 --jump ACCEPT
    done
    while "$iptables" --wait --check INPUT --in-interface '${workspaceBridge}' --source '${workspaceSubnet}' --destination '${address}' --protocol tcp --match multiport --dports 53,80,443 --jump ACCEPT 2>/dev/null; do
      "$iptables" --wait --delete INPUT --in-interface '${workspaceBridge}' --source '${workspaceSubnet}' --destination '${address}' --protocol tcp --match multiport --dports 53,80,443 --jump ACCEPT
    done
    '${pkgs.iproute2}/bin/ip' link delete '${egressInterface}' 2>/dev/null || true
  '';
in
{
  inherit
    address
    policyServiceName
    serviceName
    ;

  services = {
    "${policyServiceName}" = {
      description = "pwn.college workspace egress policy";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        Type = "oneshot";
        ExecStart = startPolicy;
        ExecStop = stopPolicy;
        RemainAfterExit = true;
      };
    };

    "${serviceName}" = {
      description = "pwn.college workspace egress proxy";
      requires = [ "${policyServiceName}.service" ];
      after = [ "${policyServiceName}.service" "network-online.target" ];
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        Type = "simple";
        ExecStart = "${package}/bin/egress";
        Environment = [
          "PWN_WORKSPACE_EGRESS_ADDRESS=${address}"
          "PWN_WORKSPACE_EGRESS_DOMAINS_FILE=${domainsFile}"
          "PWN_WORKSPACE_EGRESS_CA_CERTIFICATE=${../../../runtime/etc/ssl/certs/egress-ca.pem}"
          "PWN_WORKSPACE_EGRESS_CA_PRIVATE_KEY=${./certs/ca-key.pem}"
        ];
        AmbientCapabilities = [ "CAP_NET_BIND_SERVICE" ];
        CapabilityBoundingSet = [ "CAP_NET_BIND_SERVICE" ];
        DynamicUser = true;
        NoNewPrivileges = true;
        Restart = "on-failure";
        RestartSec = 1;
      };
    };
  };
}
