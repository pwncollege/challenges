package main

import (
	"encoding/binary"
	"net"
	"testing"

	"github.com/containernetworking/cni/pkg/skel"
	current "github.com/containernetworking/cni/pkg/types/100"
	"github.com/florianl/go-tc"
	"github.com/florianl/go-tc/core"
	"golang.org/x/sys/unix"
)

func TestSourceIdentityFromResult(t *testing.T) {
	containerIndex := 2
	result := &current.Result{
		Interfaces: []*current.Interface{
			{Name: "pwn-workspace0"},
			{Name: "lo"},
			{Name: "eth0", Mac: "02:00:00:00:00:02", Sandbox: "/test/netns"},
		},
		IPs: []*current.IPConfig{{
			Interface: &containerIndex,
			Address: net.IPNet{
				IP:   net.ParseIP("172.31.0.2"),
				Mask: net.CIDRMask(20, 32),
			},
			Gateway: net.ParseIP("172.31.0.1"),
		}},
	}
	conf := &netConf{AgentPort: 8000, Bridge: "pwn-workspace0", EgressAddress: "192.0.2.1"}
	identity, err := sourceIdentityFromResult(conf, &skel.CmdArgs{IfName: "eth0"}, result)
	if err != nil {
		t.Fatal(err)
	}
	if identity.HostInterface != "lo" || identity.MAC.String() != "02:00:00:00:00:02" || !identity.IPv4.Equal(net.ParseIP("172.31.0.2")) || !identity.Gateway.Equal(net.ParseIP("172.31.0.1")) || !identity.EgressAddress.Equal(net.ParseIP("192.0.2.1")) || identity.AgentPort != 8000 {
		t.Fatalf("source identity = %#v", identity)
	}
}

func TestPolicyFilters(t *testing.T) {
	identity := sourceIdentity{
		HostInterface: "veth-test",
		MAC:           mustMAC(t, "02:00:00:00:00:02"),
		IPv4:          net.ParseIP("172.31.0.2").To4(),
		Gateway:       net.ParseIP("172.31.0.1").To4(),
		EgressAddress: net.ParseIP("192.0.2.1").To4(),
		AgentPort:     8000,
	}
	filters := policyFilters(42, identity)
	if len(filters) != 7 {
		t.Fatalf("got %d filters", len(filters))
	}
	for _, expected := range []struct {
		index    int
		priority uint16
		protocol uint16
		kind     string
		action   uint32
	}{
		{0, 100, unix.ETH_P_ALL, "matchall", dropAction},
		{1, 10, unix.ETH_P_IP, "flower", passAction},
		{2, 20, unix.ETH_P_IP, "flower", passAction},
		{3, 30, unix.ETH_P_IP, "flower", passAction},
		{4, 40, unix.ETH_P_IP, "flower", passAction},
		{5, 50, unix.ETH_P_IP, "flower", passAction},
		{6, 60, unix.ETH_P_ARP, "flower", passAction},
	} {
		filter := filters[expected.index]
		if filter.Ifindex != 42 || filter.Parent != 0xfffffff2 || filter.Info != core.FilterInfo(expected.priority, expected.protocol) || filter.Kind != expected.kind {
			t.Errorf("filter %d = %#v", expected.index, filter)
		}
		if expected.kind == "matchall" {
			if !hasAction(filter.Matchall.Actions, expected.action) {
				t.Errorf("filter %d has wrong action", expected.index)
			}
		} else if !hasAction(filter.Flower.Actions, expected.action) {
			t.Errorf("filter %d has wrong action", expected.index)
		}
	}
	if filters[1].Flower.KeyUDPDst == nil || *filters[1].Flower.KeyUDPDst != 53 || !filters[1].Flower.KeyIPv4Dst.Equal(net.ParseIP("192.0.2.1")) {
		t.Errorf("DNS filter = %#v", filters[1].Flower)
	}
	if filters[5].Flower.KeyTCPSrc == nil || *filters[5].Flower.KeyTCPSrc != 8000 || filters[5].Flower.KeyTCPFlags == nil || *filters[5].Flower.KeyTCPFlags != 0x10 || !filters[5].Flower.KeyIPv4Dst.Equal(net.ParseIP("172.31.0.1")) {
		t.Errorf("agent reply filter = %#v", filters[5].Flower)
	}
	if filters[6].Flower.KeyArpTIP == nil || *filters[6].Flower.KeyArpTIP != binary.BigEndian.Uint32(net.ParseIP("172.31.0.1").To4()) {
		t.Errorf("ARP filter = %#v", filters[6].Flower)
	}
}

func hasAction(actions *[]*tc.Action, wanted uint32) bool {
	return actions != nil && len(*actions) == 1 && (*actions)[0].Gact != nil && (*actions)[0].Gact.Parms != nil && (*actions)[0].Gact.Parms.Action == wanted
}

func mustMAC(t *testing.T, value string) net.HardwareAddr {
	t.Helper()
	mac, err := net.ParseMAC(value)
	if err != nil {
		t.Fatal(err)
	}
	return mac
}
