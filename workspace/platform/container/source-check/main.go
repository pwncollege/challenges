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
	Bridge string `json:"bridge"`
}

type sourceIdentity struct {
	HostInterface string
	MAC           net.HardwareAddr
	IPv4          net.IP
}

func main() {
	skel.PluginMainFuncs(skel.CNIFuncs{
		Add:    cmdAdd,
		Check:  cmdCheck,
		Del:    cmdDel,
		Status: cmdStatus,
	}, version.All, "pwn.college workspace source-address check")
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
	if err := configureSourceCheck(identity); err != nil {
		return err
	}
	return types.PrintResult(result, conf.CNIVersion)
}

func cmdCheck(args *skel.CmdArgs) error {
	conf, result, err := loadConfig(args.StdinData)
	if err != nil {
		return err
	}
	identity, err := sourceIdentityFromResult(conf, args, result)
	if err != nil {
		return err
	}
	return checkSourceCheck(identity)
}

// The bridge plugin deletes the host veth after this plugin's DEL. The kernel
// deletes the veth's clsact qdisc and all of its filters with the interface.
func cmdDel(_ *skel.CmdArgs) error { return nil }

func cmdStatus(_ *skel.CmdArgs) error { return nil }

func loadConfig(data []byte) (*netConf, *current.Result, error) {
	conf := &netConf{}
	if err := json.Unmarshal(data, conf); err != nil {
		return nil, nil, fmt.Errorf("parse network configuration: %w", err)
	}
	if conf.Bridge == "" {
		return nil, nil, errors.New("bridge must not be empty")
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

	addresses := make([]net.IP, 0, 1)
	for _, ip := range result.IPs {
		if ip.Interface == nil || *ip.Interface < 0 || *ip.Interface >= len(result.Interfaces) {
			continue
		}
		intf := result.Interfaces[*ip.Interface]
		if intf.Name != args.IfName || intf.Sandbox == "" || ip.Address.IP.To4() == nil {
			continue
		}
		addresses = append(addresses, ip.Address.IP.To4())
	}
	if len(addresses) != 1 {
		return sourceIdentity{}, fmt.Errorf("expected one IPv4 address for %s, found %v", args.IfName, addresses)
	}
	if _, err := net.InterfaceByName(hostInterfaces[0]); err != nil {
		return sourceIdentity{}, fmt.Errorf("find host interface %s: %w", hostInterfaces[0], err)
	}

	return sourceIdentity{
		HostInterface: hostInterfaces[0],
		MAC:           mac,
		IPv4:          addresses[0],
	}, nil
}

func configureSourceCheck(identity sourceIdentity) error {
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
		if !errors.Is(err, unix.EEXIST) {
			return fmt.Errorf("attach clsact to %s: %w", identity.HostInterface, err)
		}
		configured, checkErr := sourceCheckConfigured(connection, intf.Index, identity)
		if checkErr != nil {
			return checkErr
		}
		if configured {
			return nil
		}
		return errors.New("host interface has an unexpected clsact qdisc")
	}

	// Install the catch-all first so a partial setup fails closed. CNI does not
	// start the container until ADD completes successfully.
	for _, filter := range sourceFilters(intf.Index, identity) {
		if err := connection.Filter().Add(&filter); err != nil {
			return fmt.Errorf("configure source check on %s: %w", identity.HostInterface, err)
		}
	}
	return nil
}

func checkSourceCheck(identity sourceIdentity) error {
	intf, err := net.InterfaceByName(identity.HostInterface)
	if err != nil {
		return fmt.Errorf("find host interface %s: %w", identity.HostInterface, err)
	}
	connection, err := tc.Open(&tc.Config{})
	if err != nil {
		return fmt.Errorf("open traffic-control netlink socket: %w", err)
	}
	defer connection.Close()
	configured, err := sourceCheckConfigured(connection, intf.Index, identity)
	if err != nil {
		return err
	}
	if !configured {
		return errors.New("workspace source check filter is missing")
	}
	return nil
}

func sourceCheckConfigured(connection *tc.Tc, interfaceIndex int, identity sourceIdentity) (bool, error) {
	qdiscs, err := connection.Qdisc().Get()
	if err != nil {
		return false, fmt.Errorf("list qdiscs: %w", err)
	}
	foundQdisc := false
	for _, qdisc := range qdiscs {
		if qdisc.Ifindex == uint32(interfaceIndex) && qdisc.Kind == "clsact" {
			foundQdisc = true
			break
		}
	}
	if !foundQdisc {
		return false, nil
	}

	filters, err := connection.Filter().Get(&tc.Msg{
		Family:  unix.AF_UNSPEC,
		Ifindex: uint32(interfaceIndex),
		Parent:  tc.HandleIngress + 1,
	})
	if err != nil {
		return false, fmt.Errorf("list source-check filters: %w", err)
	}
	for _, wanted := range sourceFilters(interfaceIndex, identity) {
		found := false
		for _, existing := range filters {
			if filterMatches(existing, wanted) {
				found = true
				break
			}
		}
		if !found {
			return false, errors.New("host interface has an incomplete source check")
		}
	}
	return true, nil
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

func sourceFilters(interfaceIndex int, identity sourceIdentity) []tc.Object {
	pass := []*tc.Action{{Kind: "gact", Gact: &tc.Gact{Parms: &tc.GactParms{Action: passAction}}}}
	drop := []*tc.Action{{Kind: "gact", Gact: &tc.Gact{Parms: &tc.GactParms{Action: dropAction}}}}
	macMask := net.HardwareAddr{0xff, 0xff, 0xff, 0xff, 0xff, 0xff}
	ipMask := net.IPv4(255, 255, 255, 255)
	ipv4 := identity.IPv4.To4()
	arpSource := binary.BigEndian.Uint32(ipv4)
	arpMask := uint32(0xffffffff)
	ipProtocol := uint16(unix.ETH_P_IP)
	arpProtocol := uint16(unix.ETH_P_ARP)
	skipHardware := uint32(tc.SkipHw)

	// The catch-all is deliberately first: configureSourceCheck applies filters
	// in this order, while their priorities still make the allow rules run first.
	return []tc.Object{
		filter(interfaceIndex, 100, unix.ETH_P_ALL, tc.Attribute{
			Kind:     "matchall",
			Matchall: &tc.Matchall{Actions: &drop, Flags: &skipHardware},
		}),
		filter(interfaceIndex, 10, unix.ETH_P_IP, tc.Attribute{
			Kind: "flower",
			Flower: &tc.Flower{
				Actions:        &pass,
				Flags:          &skipHardware,
				KeyEthSrc:      &identity.MAC,
				KeyEthSrcMask:  &macMask,
				KeyEthType:     &ipProtocol,
				KeyIPv4Src:     &ipv4,
				KeyIPv4SrcMask: &ipMask,
			},
		}),
		filter(interfaceIndex, 20, unix.ETH_P_ARP, tc.Attribute{
			Kind: "flower",
			Flower: &tc.Flower{
				Actions:       &pass,
				Flags:         &skipHardware,
				KeyEthSrc:     &identity.MAC,
				KeyEthSrcMask: &macMask,
				KeyEthType:    &arpProtocol,
				KeyArpSIP:     &arpSource,
				KeyArpSIPMask: &arpMask,
			},
		}),
	}
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

func filterMatches(existing, wanted tc.Object) bool {
	if existing.Ifindex != wanted.Ifindex || existing.Parent != wanted.Parent || existing.Info != wanted.Info || existing.Kind != wanted.Kind {
		return false
	}
	if wanted.Matchall != nil {
		return existing.Matchall != nil && actionMatches(existing.Matchall.Actions, dropAction)
	}
	if existing.Flower == nil || wanted.Flower == nil || !actionMatches(existing.Flower.Actions, passAction) {
		return false
	}
	if !hardwareAddressEqual(existing.Flower.KeyEthSrc, wanted.Flower.KeyEthSrc) {
		return false
	}
	if !hardwareAddressEqual(existing.Flower.KeyEthSrcMask, wanted.Flower.KeyEthSrcMask) || !uint16Equal(existing.Flower.KeyEthType, wanted.Flower.KeyEthType) {
		return false
	}
	if wanted.Flower.KeyIPv4Src != nil {
		return existing.Flower.KeyIPv4Src != nil && (*existing.Flower.KeyIPv4Src).Equal(*wanted.Flower.KeyIPv4Src) && existing.Flower.KeyIPv4SrcMask != nil && (*existing.Flower.KeyIPv4SrcMask).Equal(*wanted.Flower.KeyIPv4SrcMask)
	}
	return uint32Equal(existing.Flower.KeyArpSIP, wanted.Flower.KeyArpSIP) && uint32Equal(existing.Flower.KeyArpSIPMask, wanted.Flower.KeyArpSIPMask)
}

func actionMatches(actions *[]*tc.Action, wanted uint32) bool {
	return actions != nil && len(*actions) == 1 && (*actions)[0].Gact != nil && (*actions)[0].Gact.Parms != nil && (*actions)[0].Gact.Parms.Action == wanted
}

func hardwareAddressEqual(left, right *net.HardwareAddr) bool {
	return left != nil && right != nil && (*left).String() == (*right).String()
}

func uint32Equal(left, right *uint32) bool {
	return left != nil && right != nil && *left == *right
}

func uint16Equal(left, right *uint16) bool {
	return left != nil && right != nil && *left == *right
}
