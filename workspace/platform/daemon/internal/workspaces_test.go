package daemon

import (
	"slices"
	"testing"
)

func TestWorkspaceVolumeContainerConfig(t *testing.T) {
	s := &Server{config: Config{
		egressAddress:  "192.0.2.1",
		logDirectory:   "/run/pwn.college/logs",
		nixStorePath:   "/var/lib/pwn.college/workspace-closures/test/store",
		seccompProfile: "/nix/store/test-seccomp.json",
		workspacePath:  "/nix/store/test-workspace",
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
	_, container := s.workspaceContainerConfig(
		"99999999-9999-4999-8999-999999999999",
		body,
		"/volumes/88888888-8888-4888-8888-888888888888/active",
	)
	capabilities := container.Linux.SecurityContext.Capabilities.AddCapabilities
	for _, capability := range []string{"SYS_ADMIN", "NET_ADMIN"} {
		if !slices.Contains(capabilities, capability) {
			t.Fatalf("capabilities = %v, want %s", capabilities, capability)
		}
	}
	if len(container.Mounts) != 2 || container.Mounts[1].ContainerPath != "/home/hacker" {
		t.Fatalf("mounts = %#v", container.Mounts)
	}
}

func TestWorkspaceStartDoesNotRequireFlag(t *testing.T) {
	err := validateWorkspaceStart(workspaceStartRequest{
		RuntimeConfig: runtimeConfig{ContainerImageRef: "test-workspace:latest"},
	}, false)
	if err != nil {
		t.Fatal(err)
	}
}
