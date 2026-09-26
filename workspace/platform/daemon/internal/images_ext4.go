package daemon

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/klauspost/compress/zstd"
)

// Kata passes this regular raw image to QEMU and mounts ext4 inside the guest.
// The host only creates and copies image files; it does not mount their contents.
func registerVolume(ctx context.Context, path string) error {
	info, err := os.Stat(filepath.Join(path, "home.ext4"))
	if err != nil {
		return err
	}
	if !info.Mode().IsRegular() {
		return fmt.Errorf("home image is not a regular file")
	}
	mountInfo, err := json.Marshal(map[string]any{
		"volume-type": "blk", "device": filepath.Join(path, "home.ext4"), "fstype": "ext4",
		"options": []string{"rw", "nosuid", "nodev"},
	})
	if err != nil {
		return err
	}
	// Discard sandbox metadata from the previous attachment. The caller has
	// confirmed that no CRI sandbox is using this volume.
	if err := unregisterVolume(ctx, path); err != nil {
		return err
	}
	return runVolumeCommand(ctx, "kata-runtime", "direct-volume", "add", "--volume-path", path, "--mount-info", string(mountInfo))
}

func unregisterVolume(ctx context.Context, path string) error {
	return runVolumeCommand(ctx, "kata-runtime", "direct-volume", "remove", "--volume-path", path)
}

func runVolumeCommand(ctx context.Context, name string, args ...string) error {
	output, err := exec.CommandContext(ctx, name, args...).CombinedOutput()
	if err != nil {
		return fmt.Errorf("%s: %w: %s", name, err, bytes.TrimSpace(output))
	}
	return nil
}

func createImage(ctx context.Context, path string, size int64) error {
	file, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_RDWR, 0600)
	if err != nil {
		return err
	}
	defer file.Close()
	if err := file.Truncate(size); err != nil {
		return err
	}
	if err := runVolumeCommand(ctx, "mkfs.ext4", "-q", "-F", "-m", "0", "-b", "4096",
		"-E", "root_owner=1000:1000,lazy_itable_init=0,lazy_journal_init=0", path); err != nil {
		return err
	}
	return file.Sync()
}

// Call only after the VM has stopped and released the disk. The resulting file
// is immutable and is published only after compression and fsync finish.
func captureImage(ctx context.Context, image, snapshot string) error {
	source, err := os.Open(image)
	if err != nil {
		return err
	}
	defer source.Close()
	return publishFile(snapshot, func(file *os.File) error {
		encoder, err := zstd.NewWriter(file, zstd.WithEncoderConcurrency(1))
		if err != nil {
			return err
		}
		_, copyErr := io.Copy(encoder, contextReader{ctx, source})
		closeErr := encoder.Close()
		if copyErr != nil {
			return copyErr
		}
		return closeErr
	})
}

// Restore a sparse file, retaining holes for zero-filled chunks. Limit both the
// decompressed size and decoder memory before publishing a home to Kata.
func restoreImage(ctx context.Context, snapshot, image string, size int64) error {
	source, err := os.Open(snapshot)
	if err != nil {
		return err
	}
	defer source.Close()
	decoder, err := zstd.NewReader(source, zstd.WithDecoderConcurrency(1), zstd.WithDecoderMaxMemory(64<<20))
	if err != nil {
		return err
	}
	defer decoder.Close()
	return publishFile(image, func(file *os.File) error {
		reader := io.LimitReader(contextReader{ctx, decoder}, size+1)
		buffer, zero := make([]byte, 1<<20), make([]byte, 1<<20)
		var total int64
		for {
			n, readErr := reader.Read(buffer)
			total += int64(n)
			if total > size {
				return fmt.Errorf("snapshot exceeds volume size")
			}
			if bytes.Equal(buffer[:n], zero[:n]) {
				if _, err := file.Seek(int64(n), io.SeekCurrent); err != nil {
					return err
				}
			} else if _, err := file.Write(buffer[:n]); err != nil {
				return err
			}
			if readErr == io.EOF {
				break
			}
			if readErr != nil {
				return readErr
			}
		}
		if total != size {
			return fmt.Errorf("snapshot size %d does not match volume size %d", total, size)
		}
		return file.Truncate(total)
	})
}

func publishFile(path string, write func(*os.File) error) error {
	file, err := os.CreateTemp(filepath.Dir(path), ".partial-")
	if err != nil {
		return err
	}
	defer os.Remove(file.Name())
	defer file.Close()
	if err := write(file); err != nil {
		return err
	}
	if err := file.Sync(); err != nil {
		return err
	}
	if err := file.Close(); err != nil {
		return err
	}
	if err := os.Rename(file.Name(), path); err != nil {
		return err
	}
	return syncDirectory(filepath.Dir(path))
}

type contextReader struct {
	ctx    context.Context
	reader io.Reader
}

func (r contextReader) Read(buffer []byte) (int, error) {
	if err := r.ctx.Err(); err != nil {
		return 0, err
	}
	return r.reader.Read(buffer)
}
