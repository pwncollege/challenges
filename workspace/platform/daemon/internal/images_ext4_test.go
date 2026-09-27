package daemon

import (
	"bytes"
	"context"
	"crypto/rand"
	"crypto/sha256"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/klauspost/compress/zstd"
	"golang.org/x/sys/unix"
)

func TestExt4ImageTransfer(t *testing.T) {
	ctx := context.Background()
	dir := t.TempDir()
	source, restored := filepath.Join(dir, "home.ext4"), filepath.Join(dir, "restored.ext4")
	const size = 64 << 20
	if err := createImage(ctx, source, size); err != nil {
		t.Fatal(err)
	}
	info, err := exec.Command("debugfs", "-R", "stat /", source).CombinedOutput()
	if err != nil || !strings.Contains(string(info), "1000") {
		t.Fatalf("root owner: %s (%v)", info, err)
	}
	marker := filepath.Join(dir, "marker")
	if err := os.WriteFile(marker, []byte("persistent home contents"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := runVolumeCommand(ctx, "debugfs", "-w", "-R", "write "+marker+" /marker", source); err != nil {
		t.Fatal(err)
	}
	snapshot, err := captureImage(ctx, source)
	if err != nil {
		t.Fatal(err)
	}
	defer snapshot.Close()
	link, err := os.Readlink(fmt.Sprintf("/proc/self/fd/%d", snapshot.Fd()))
	if err != nil || !strings.HasPrefix(link, "/memfd:workspace-snapshot") {
		t.Fatalf("snapshot is not a memfd: %q, %v", link, err)
	}
	seals, err := unix.FcntlInt(snapshot.Fd(), unix.F_GET_SEALS, 0)
	if err != nil || seals&(unix.F_SEAL_WRITE|unix.F_SEAL_GROW|unix.F_SEAL_SHRINK) != unix.F_SEAL_WRITE|unix.F_SEAL_GROW|unix.F_SEAL_SHRINK {
		t.Fatalf("snapshot is not sealed: %d, %v", seals, err)
	}
	var uploaded []byte
	transfer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodPut {
			var err error
			uploaded, err = io.ReadAll(r.Body)
			if err != nil {
				t.Error(err)
			}
			if r.ContentLength != int64(len(uploaded)) || len(r.TransferEncoding) != 0 {
				t.Errorf("upload length = %d, transfer = %v", r.ContentLength, r.TransferEncoding)
			}
		} else {
			_, _ = w.Write(uploaded)
		}
	}))
	defer transfer.Close()
	if err := uploadSnapshot(ctx, snapshot, transfer.URL); err != nil {
		t.Fatal(err)
	}
	if err := downloadSnapshot(ctx, transfer.URL, restored, size); err != nil {
		t.Fatal(err)
	}
	digest := func(path string) [32]byte {
		t.Helper()
		file, err := os.Open(path)
		if err != nil {
			t.Fatal(err)
		}
		defer file.Close()
		hash := sha256.New()
		if _, err := io.Copy(hash, file); err != nil {
			t.Fatal(err)
		}
		return [32]byte(hash.Sum(nil))
	}
	if digest(source) != digest(restored) {
		t.Fatal("restored image differs from source")
	}
	contents, err := exec.Command("debugfs", "-R", "cat /marker", restored).CombinedOutput()
	if err != nil || !bytes.Contains(contents, []byte("persistent home contents")) {
		t.Fatalf("restored contents: %s (%v)", contents, err)
	}
	if err := runVolumeCommand(ctx, "e2fsck", "-fn", restored); err != nil {
		t.Fatal(err)
	}
}

func TestRestoreRejectsInvalidImagesWithoutPublishing(t *testing.T) {
	encoder, err := zstd.NewWriter(nil)
	if err != nil {
		t.Fatal(err)
	}
	defer encoder.Close()
	data := encoder.EncodeAll(bytes.Repeat([]byte("home"), 1024), nil)
	for _, tc := range []struct {
		name string
		data []byte
		size int64
	}{
		{"short", data, 8192},
		{"oversize", data, 1024},
		{"truncated", data[:len(data)-1], 4096},
		{"invalid", []byte("not a snapshot"), 4096},
	} {
		t.Run(tc.name, func(t *testing.T) {
			dir := t.TempDir()
			image := filepath.Join(dir, "image")
			if err := restoreImage(context.Background(), bytes.NewReader(tc.data), image, tc.size); err == nil {
				t.Fatal("invalid image accepted")
			}
			if _, err := os.Stat(image); !os.IsNotExist(err) {
				t.Fatalf("published invalid image: %v", err)
			}
			partials, _ := filepath.Glob(filepath.Join(dir, ".partial-*"))
			if len(partials) != 0 {
				t.Fatalf("left partial images: %v", partials)
			}
		})
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	dir := t.TempDir()
	source := filepath.Join(dir, "source")
	if err := os.WriteFile(source, data, 0600); err != nil {
		t.Fatal(err)
	}
	if file, err := captureImage(ctx, source); err == nil || file != nil {
		t.Fatal("cancelled capture succeeded")
	}
}

func TestIncompressibleSnapshotAndCancelledCaptureCleanup(t *testing.T) {
	dir := t.TempDir()
	source := filepath.Join(dir, "home.ext4")
	data := make([]byte, 1<<20)
	if _, err := rand.Read(data); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(source, data, 0600); err != nil {
		t.Fatal(err)
	}
	snapshot, err := captureImage(context.Background(), source)
	if err != nil {
		t.Fatal(err)
	}
	defer snapshot.Close()
	info, err := snapshot.Stat()
	if err != nil {
		t.Fatal(err)
	}
	if info.Size() <= int64(len(data)) || info.Size() > maxSnapshotSize(int64(len(data))) {
		t.Fatalf("incompressible snapshot size: %d", info.Size())
	}
	decoder, err := zstd.NewReader(snapshot)
	if err != nil {
		t.Fatal(err)
	}
	defer decoder.Close()
	restored, err := io.ReadAll(decoder)
	if err != nil || !bytes.Equal(restored, data) {
		t.Fatalf("incompressible data did not round trip: %v", err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	before, _ := os.ReadDir("/proc/self/fd")
	for range 5 {
		if file, err := captureImage(ctx, source); err == nil || file != nil {
			t.Fatal("cancelled capture succeeded")
		}
	}
	after, _ := os.ReadDir("/proc/self/fd")
	if len(after) != len(before) {
		t.Fatalf("failed captures leaked descriptors: %d -> %d", len(before), len(after))
	}
	files, _ := os.ReadDir(dir)
	if len(files) != 1 {
		t.Fatalf("compressed files written to disk: %v", files)
	}
}
