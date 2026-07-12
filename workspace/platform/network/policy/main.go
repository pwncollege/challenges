package main

import (
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"net"

	"github.com/containernetworking/cni/pkg/skel"
	"github.com/containernetworking/cni/pkg/types"
	current "github.com/containernetworking/cni/pkg/types/100"
	"github.com/containernetworking/cni/pkg/version"
	"github.com/florianl/go-tc"
	"github.com/florianl/go-tc/core"
	"golang.org/x/sys/unix"
)

const (
	passAction = 0
	dropAction = 2
)

type netConf struct {
	types.NetConf
	AgentPort     uint16 `json:"agentPort"`
	Bridge        string `json:"bridge"`
	EgressAddress string `json:"egressAddress"`
}

type sourceIdentity struct {
	HostInterface string
	MAC           net.HardwareAddr
	IPv4          net.IP
	Gateway       net.IP
	EgressAddress net.IP
	AgentPort     uint16
}

func main() {
	skel.PluginMainFuncs(skel.CNIFuncs{
		Add: cmdAdd,
		Del: cmdDel,
	}, version.All, "pwn.college workspace network policy")
}

func cmdAdd(args *skel.CmdArgs) error {
	conf, result, err := loadConfig(args.StdinData)
	if err != nil {
		return err
	}
	identity, err := sourceIdentityFromResult(conf, args, result)
	if err != nil {
		return err
	}
	if err := configureNetworkPolicy(identity); err != nil {
		return err
	}
	return types.PrintResult(result, conf.CNIVersion)
}

// The bridge plugin deletes the host veth after this plugin's DEL. The kernel
// deletes the veth's clsact qdisc and all of its filters with the interface.
func cmdDel(_ *skel.CmdArgs) error { return nil }

func loadConfig(data []byte) (*netConf, *current.Result, error) {
	conf := &netConf{}
	if err := json.Unmarshal(data, conf); err != nil {
		return nil, nil, fmt.Errorf("parse network configuration: %w", err)
	}
	if conf.Bridge == "" {
		return nil, nil, errors.New("bridge must not be empty")
	}
	if net.ParseIP(conf.EgressAddress).To4() == nil {
		return nil, nil, errors.New("egressAddress must be an IPv4 address")
	}
	if conf.AgentPort == 0 {
		return nil, nil, errors.New("agentPort must not be zero")
	}
	if conf.RawPrevResult == nil {
		return nil, nil, errors.New("prevResult is required")
	}
	if err := version.ParsePrevResult(&conf.NetConf); err != nil {
		return nil, nil, fmt.Errorf("parse prevResult: %w", err)
	}
	result, err := current.NewResultFromResult(conf.PrevResult)
	if err != nil {
		return nil, nil, fmt.Errorf("convert prevResult: %w", err)
	}
	return conf, result, nil
}

func sourceIdentityFromResult(conf *netConf, args *skel.CmdArgs, result *current.Result) (sourceIdentity, error) {
	hostInterfaces := make([]string, 0, 1)
	var containerInterface *current.Interface
	for _, intf := range result.Interfaces {
		switch {
		case intf.Name == args.IfName && intf.Sandbox != "":
			if containerInterface != nil {
				return sourceIdentity{}, fmt.Errorf("found multiple container interfaces named %s", args.IfName)
			}
			containerInterface = intf
		case intf.Sandbox == "" && intf.Name != conf.Bridge:
			hostInterfaces = append(hostInterfaces, intf.Name)
		}
	}
	if len(hostInterfaces) != 1 {
		return sourceIdentity{}, fmt.Errorf("expected one host interface, found %v", hostInterfaces)
	}
	if containerInterface == nil {
		return sourceIdentity{}, fmt.Errorf("container interface %s is missing", args.IfName)
	}
	mac, err := net.ParseMAC(containerInterface.Mac)
	if err != nil {
		return sourceIdentity{}, fmt.Errorf("parse container MAC address %q: %w", containerInterface.Mac, err)
	}

	type address struct {
		ip      net.IP
		gateway net.IP
	}
	addresses := make([]address, 0, 1)
	for _, ip := range result.IPs {
		if ip.Interface == nil || *ip.Interface < 0 || *ip.Interface >= len(result.Interfaces) {
			continue
		}
		intf := result.Interfaces[*ip.Interface]
		if intf.Name != args.IfName || intf.Sandbox == "" || ip.Address.IP.To4() == nil {
			continue
		}
		gateway := ip.Gateway.To4()
		if gateway == nil {
			continue
		}
		addresses = append(addresses, address{ip: ip.Address.IP.To4(), gateway: gateway})
	}
	if len(addresses) != 1 {
		return sourceIdentity{}, fmt.Errorf("expected one IPv4 address for %s, found %v", args.IfName, addresses)
	}
	return sourceIdentity{
		HostInterface: hostInterfaces[0],
		MAC:           mac,
		IPv4:          addresses[0].ip,
		Gateway:       addresses[0].gateway,
		EgressAddress: net.ParseIP(conf.EgressAddress).To4(),
		AgentPort:     conf.AgentPort,
	}, nil
}

func configureNetworkPolicy(identity sourceIdentity) error {
	intf, err := net.InterfaceByName(identity.HostInterface)
	if err != nil {
		return fmt.Errorf("find host interface %s: %w", identity.HostInterface, err)
	}
	connection, err := tc.Open(&tc.Config{})
	if err != nil {
		return fmt.Errorf("open traffic-control netlink socket: %w", err)
	}
	defer connection.Close()

	qdisc := clsactQdisc(intf.Index)
	if err := connection.Qdisc().Add(&qdisc); err != nil {
		if errors.Is(err, unix.EEXIST) {
			return nil
		}
		return fmt.Errorf("attach clsact to %s: %w", identity.HostInterface, err)
	}

	// Install the catch-all first so a partial setup fails closed. CNI does not
	// start the container until ADD completes successfully.
	for _, filter := range policyFilters(intf.Index, identity) {
		if err := connection.Filter().Add(&filter); err != nil {
			return fmt.Errorf("configure network policy on %s: %w", identity.HostInterface, err)
		}
	}
	return nil
}

func clsactQdisc(interfaceIndex int) tc.Object {
	return tc.Object{
		Msg: tc.Msg{
			Family:  unix.AF_UNSPEC,
			Ifindex: uint32(interfaceIndex),
			Handle:  core.BuildHandle(tc.HandleRoot, 0),
			Parent:  tc.HandleIngress,
		},
		Attribute: tc.Attribute{Kind: "clsact"},
	}
}

func policyFilters(interfaceIndex int, identity sourceIdentity) []tc.Object {
	pass := []*tc.Action{{Kind: "gact", Gact: &tc.Gact{Parms: &tc.GactParms{Action: passAction}}}}
	drop := []*tc.Action{{Kind: "gact", Gact: &tc.Gact{Parms: &tc.GactParms{Action: dropAction}}}}
	ipv4 := identity.IPv4.To4()
	arpSource := binary.BigEndian.Uint32(ipv4)
	arpTarget := binary.BigEndian.Uint32(identity.Gateway.To4())
	arpMask := uint32(0xffffffff)
	arpProtocol := uint16(unix.ETH_P_ARP)
	skipHardware := uint32(tc.SkipHw)
	ack := uint16(0x10)

	// The catch-all is deliberately first: configureNetworkPolicy applies filters
	// in this order, while their priorities still make the allow rules run first.
	return []tc.Object{
		filter(interfaceIndex, 100, unix.ETH_P_ALL, tc.Attribute{
			Kind:     "matchall",
			Matchall: &tc.Matchall{Actions: &drop, Flags: &skipHardware},
		}),
		ipv4Filter(interfaceIndex, 10, identity, unix.IPPROTO_UDP, 0, 53, 0, 0, identity.EgressAddress, pass),
		ipv4Filter(interfaceIndex, 20, identity, unix.IPPROTO_TCP, 0, 53, 0, 0, identity.EgressAddress, pass),
		ipv4Filter(interfaceIndex, 30, identity, unix.IPPROTO_TCP, 0, 80, 0, 0, identity.EgressAddress, pass),
		ipv4Filter(interfaceIndex, 40, identity, unix.IPPROTO_TCP, 0, 443, 0, 0, identity.EgressAddress, pass),
		ipv4Filter(interfaceIndex, 50, identity, unix.IPPROTO_TCP, identity.AgentPort, 0, ack, ack, identity.Gateway, pass),
		filter(interfaceIndex, 60, unix.ETH_P_ARP, tc.Attribute{
			Kind: "flower",
			Flower: &tc.Flower{
				Actions:       &pass,
				Flags:         &skipHardware,
				KeyEthSrc:     &identity.MAC,
				KeyEthSrcMask: fullMACMask(),
				KeyEthType:    &arpProtocol,
				KeyArpSIP:     &arpSource,
				KeyArpSIPMask: &arpMask,
				KeyArpTIP:     &arpTarget,
				KeyArpTIPMask: &arpMask,
			},
		}),
	}
}

func ipv4Filter(interfaceIndex int, priority uint16, identity sourceIdentity, protocol uint8, sourcePort, destinationPort, tcpFlags, tcpFlagsMask uint16, destination net.IP, actions []*tc.Action) tc.Object {
	ipProtocol := uint16(unix.ETH_P_IP)
	skipHardware := uint32(tc.SkipHw)
	ipMask := net.IPv4(255, 255, 255, 255)
	flower := &tc.Flower{
		Actions:        &actions,
		Flags:          &skipHardware,
		KeyEthSrc:      &identity.MAC,
		KeyEthSrcMask:  fullMACMask(),
		KeyEthType:     &ipProtocol,
		KeyIPProto:     &protocol,
		KeyIPv4Src:     &identity.IPv4,
		KeyIPv4SrcMask: &ipMask,
		KeyIPv4Dst:     &destination,
		KeyIPv4DstMask: &ipMask,
	}
	if protocol == unix.IPPROTO_TCP {
		if sourcePort != 0 {
			flower.KeyTCPSrc = &sourcePort
		}
		if destinationPort != 0 {
			flower.KeyTCPDst = &destinationPort
		}
		if tcpFlagsMask != 0 {
			flower.KeyTCPFlags = &tcpFlags
			flower.KeyTCPFlagsMask = &tcpFlagsMask
		}
	} else {
		flower.KeyUDPDst = &destinationPort
	}
	return filter(interfaceIndex, priority, unix.ETH_P_IP, tc.Attribute{Kind: "flower", Flower: flower})
}

func fullMACMask() *net.HardwareAddr {
	mask := net.HardwareAddr{0xff, 0xff, 0xff, 0xff, 0xff, 0xff}
	return &mask
}

func filter(interfaceIndex int, priority, protocol uint16, attribute tc.Attribute) tc.Object {
	return tc.Object{
		Msg: tc.Msg{
			Family:  unix.AF_UNSPEC,
			Ifindex: uint32(interfaceIndex),
			Handle:  1,
			Parent:  tc.HandleIngress + 1,
			Info:    core.FilterInfo(priority, protocol),
		},
		Attribute: attribute,
	}
}
