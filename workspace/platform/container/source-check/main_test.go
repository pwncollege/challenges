package main

import (
	"net"
	"testing"

	"github.com/containernetworking/cni/pkg/skel"
	current "github.com/containernetworking/cni/pkg/types/100"
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
		}},
	}
	conf := &netConf{Bridge: "pwn-workspace0"}
	identity, err := sourceIdentityFromResult(conf, &skel.CmdArgs{IfName: "eth0"}, result)
	if err != nil {
		t.Fatal(err)
	}
	if identity.HostInterface != "lo" || identity.MAC.String() != "02:00:00:00:00:02" || !identity.IPv4.Equal(net.ParseIP("172.31.0.2")) {
		t.Fatalf("source identity = %#v", identity)
	}
}

func TestSourceFilters(t *testing.T) {
	identity := sourceIdentity{
		HostInterface: "veth-test",
		MAC:           mustMAC(t, "02:00:00:00:00:02"),
		IPv4:          net.ParseIP("172.31.0.2").To4(),
	}
	filters := sourceFilters(42, identity)
	if len(filters) != 3 {
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
		{2, 20, unix.ETH_P_ARP, "flower", passAction},
	} {
		filter := filters[expected.index]
		if filter.Ifindex != 42 || filter.Parent != 0xfffffff2 || filter.Info != core.FilterInfo(expected.priority, expected.protocol) || filter.Kind != expected.kind {
			t.Errorf("filter %d = %#v", expected.index, filter)
		}
		if expected.kind == "matchall" {
			if !actionMatches(filter.Matchall.Actions, expected.action) {
				t.Errorf("filter %d has wrong action", expected.index)
			}
		} else if !actionMatches(filter.Flower.Actions, expected.action) {
			t.Errorf("filter %d has wrong action", expected.index)
		}
	}
}

func mustMAC(t *testing.T, value string) net.HardwareAddr {
	t.Helper()
	mac, err := net.ParseMAC(value)
	if err != nil {
		t.Fatal(err)
	}
	return mac
}
