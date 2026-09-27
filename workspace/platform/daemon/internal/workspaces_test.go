package daemon

import (
	"bytes"
	"context"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"slices"
	"testing"

	"github.com/klauspost/compress/zstd"
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

func TestExportRetryRecompressesRetiredImageAfterRestart(t *testing.T) {
	const volumeUUID = "88888888-8888-4888-8888-888888888888"
	const snapshotUUID = "99999999-9999-4999-8999-999999999999"
	cfg := Config{volumeBasePath: t.TempDir()}
	retired := filepath.Join(cfg.volumeBasePath, volumeUUID, "retired", snapshotUUID)
	active := filepath.Join(cfg.volumeBasePath, volumeUUID, "active")
	for path, contents := range map[string]string{retired: "original home", active: "newer home"} {
		if err := os.MkdirAll(path, 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(path, "home.ext4"), []byte(contents), 0600); err != nil {
			t.Fatal(err)
		}
	}
	var payloads [][]byte
	transfer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, err := io.ReadAll(r.Body)
		if err != nil {
			t.Error(err)
		}
		payloads = append(payloads, body)
		if len(payloads) == 1 {
			w.WriteHeader(http.StatusServiceUnavailable)
		}
	}))
	defer transfer.Close()
	for attempt := range 2 {
		// No in-memory state survives between the failed upload and its retry.
		s := New(cfg, nil, nil)
		err := s.exportVolume(context.Background(), volumeUUID, snapshotUUID, volumeExportRequest{UploadURL: transfer.URL})
		if (err != nil) != (attempt == 0) {
			t.Fatalf("attempt %d: %v", attempt, err)
		}
	}
	if len(payloads) != 2 || !bytes.Equal(payloads[0], payloads[1]) {
		t.Fatal("retry changed snapshot contents")
	}
	decoder, err := zstd.NewReader(nil)
	if err != nil {
		t.Fatal(err)
	}
	defer decoder.Close()
	contents, err := decoder.DecodeAll(payloads[1], nil)
	if err != nil || string(contents) != "original home" {
		t.Fatalf("snapshot = %q, %v", contents, err)
	}
	newer, err := os.ReadFile(filepath.Join(active, "home.ext4"))
	if err != nil || string(newer) != "newer home" {
		t.Fatalf("active home changed: %q, %v", newer, err)
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

func TestPrepareVolumeReusesLocalAndDoesNotReplaceFailedDownloadWithEmptyHome(t *testing.T) {
	s := &Server{config: Config{volumeBasePath: t.TempDir()}}
	volume := workspaceVolume{VolumeUUID: "88888888-8888-4888-8888-888888888888", MaxSizeBytes: 64 << 20}
	source := httptest.NewServer(http.NotFoundHandler())
	defer source.Close()
	volume.Snapshot = &volumeSnapshot{SnapshotUUID: "99999999-9999-4999-8999-999999999999", DownloadURL: source.URL}
	active := s.activePath(volume.VolumeUUID)
	if err := os.MkdirAll(active, 0700); err != nil {
		t.Fatal(err)
	}
	if got, err := s.prepareVolume(context.Background(), volume); err != nil || got != active {
		t.Fatalf("reuse = %q, %v", got, err)
	}
	if err := os.Remove(active); err != nil {
		t.Fatal(err)
	}
	if _, err := s.prepareVolume(context.Background(), volume); err == nil {
		t.Fatal("failed snapshot download succeeded")
	}
	if _, err := os.Stat(active); !os.IsNotExist(err) {
		t.Fatalf("active home published after failed download: %v", err)
	}
	if err := recordRequest(filepath.Join(s.volumeRoot(volume.VolumeUUID), ".exporting"), "pending"); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(active, 0700); err != nil {
		t.Fatal(err)
	}
	if _, err := s.prepareVolume(context.Background(), volume); err == nil {
		t.Fatal("reused a home with an incomplete export")
	}
}
