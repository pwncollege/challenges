package daemon

import (
	"net/netip"
	"slices"
	"testing"
)

func TestWorkspaceVolumeContainerConfig(t *testing.T) {
	s := &Server{config: Config{
		dockerNetwork: "workspace-test",
		nixStorePath:  "/var/lib/pwn.college/workspace-closures/test/store",
		workspacePath: "/nix/store/test-workspace",
	}}
	body := workspaceStartRequest{
		RuntimeConfig: runtimeConfig{
			ContainerImageRef: "test-workspace:latest",
			Env:               map[string]string{"PWN_FLAG": "pwn.college{test}"},
		},
		Volume: &workspaceVolume{
			VolumeUUID: "88888888-8888-4888-8888-888888888888",
			DstPath:    "/home/hacker",
		},
	}
	_, host, _ := s.workspaceContainerConfig(
		"99999999-9999-4999-8999-999999999999",
		netip.MustParseAddr("192.0.2.2"),
		body,
		"/volumes/88888888-8888-4888-8888-888888888888/active",
	)
	capabilities := []string(host.CapAdd)
	for _, capability := range []string{"SYS_ADMIN", "NET_ADMIN"} {
		if !slices.Contains(capabilities, capability) {
			t.Fatalf("capabilities = %v, want %s", capabilities, capability)
		}
	}
	if len(host.Mounts) != 2 || host.Mounts[1].Target != "/home/hacker" {
		t.Fatalf("mounts = %#v", host.Mounts)
	}
}
