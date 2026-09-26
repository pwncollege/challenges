package daemon

import (
	"bytes"
	"context"
	"crypto/sha256"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/klauspost/compress/zstd"
)

func TestExt4ImageTransfer(t *testing.T) {
	ctx := context.Background()
	dir := t.TempDir()
	source, snapshot, received, restored := filepath.Join(dir, "home.ext4"), filepath.Join(dir, "snapshot.zst"), filepath.Join(dir, "received.zst"), filepath.Join(dir, "restored.ext4")
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
	if err := captureImage(ctx, source, snapshot); err != nil {
		t.Fatal(err)
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
	if err := downloadSnapshot(ctx, transfer.URL, received, size); err != nil {
		t.Fatal(err)
	}
	if err := restoreImage(ctx, received, restored, size); err != nil {
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
			snapshot, image := filepath.Join(dir, "snapshot"), filepath.Join(dir, "image")
			if err := os.WriteFile(snapshot, tc.data, 0600); err != nil {
				t.Fatal(err)
			}
			if err := restoreImage(context.Background(), snapshot, image, tc.size); err == nil {
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
	source, snapshot := filepath.Join(dir, "source"), filepath.Join(dir, "snapshot")
	if err := os.WriteFile(source, data, 0600); err != nil {
		t.Fatal(err)
	}
	if err := captureImage(ctx, source, snapshot); err == nil {
		t.Fatal("cancelled capture succeeded")
	}
	if _, err := os.Stat(snapshot); !os.IsNotExist(err) {
		t.Fatalf("published cancelled capture: %v", err)
	}
}
