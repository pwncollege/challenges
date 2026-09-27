package daemon

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/klauspost/compress/zstd"
	"golang.org/x/sys/unix"
)

// Kata opens image files as virtual disks and mounts them inside the guest.
// The host never mounts their contents.
func registerDisk(image, fstype string, options ...string) error {
	info, err := os.Stat(image)
	if err != nil {
		return err
	}
	if !info.Mode().IsRegular() {
		return fmt.Errorf("image %s is not a regular file", image)
	}
	mountInfo, err := json.Marshal(map[string]any{
		"volume-type": "directvol", "device": image, "fstype": fstype, "options": options,
	})
	if err != nil {
		return err
	}
	directory := directVolumePath(image)
	if err := os.MkdirAll(directory, 0700); err != nil {
		return err
	}
	return publishFile(filepath.Join(directory, "mountInfo.json"), func(file *os.File) error {
		_, err := file.Write(mountInfo)
		return err
	})
}

func unregisterDisk(image string) error {
	return os.RemoveAll(directVolumePath(image))
}

func directVolumePath(path string) string {
	return filepath.Join("/run/kata-containers/shared/direct-volumes", base64.URLEncoding.EncodeToString([]byte(path)))
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

// Compress a detached image into a bounded, anonymous file. Sealing makes the
// completed payload immutable; closing it releases its memory.
func captureImage(ctx context.Context, image string) (_ *os.File, err error) {
	source, err := os.Open(image)
	if err != nil {
		return nil, err
	}
	defer source.Close()
	info, err := source.Stat()
	if err != nil {
		return nil, err
	}
	limit := maxSnapshotSize(info.Size())
	fd, err := unix.MemfdCreate("workspace-snapshot", unix.MFD_CLOEXEC|unix.MFD_ALLOW_SEALING)
	if err != nil {
		return nil, err
	}
	file := os.NewFile(uintptr(fd), "workspace-snapshot")
	defer func() {
		if err != nil {
			file.Close()
		}
	}()
	// Sparse length plus a grow seal bounds RAM by image size and compression
	// overhead. Setting the length itself does not allocate RAM.
	if err = file.Truncate(limit); err != nil {
		return nil, err
	}
	if _, err = unix.FcntlInt(file.Fd(), unix.F_ADD_SEALS, unix.F_SEAL_GROW); err != nil {
		return nil, err
	}
	encoder, err := zstd.NewWriter(file, zstd.WithEncoderConcurrency(1))
	if err != nil {
		return nil, err
	}
	copied, copyErr := io.Copy(encoder, contextReader{ctx, io.LimitReader(source, info.Size()+1)})
	closeErr := encoder.Close()
	if copyErr != nil {
		return nil, fmt.Errorf("compress snapshot (memory limit %d bytes): %w", limit, copyErr)
	}
	if closeErr != nil {
		return nil, fmt.Errorf("compress snapshot (memory limit %d bytes): %w", limit, closeErr)
	}
	if copied != info.Size() {
		return nil, fmt.Errorf("home image size changed during export")
	}
	size, err := file.Seek(0, io.SeekCurrent)
	if err != nil {
		return nil, err
	}
	if err = file.Truncate(size); err != nil {
		return nil, err
	}
	if _, err = unix.FcntlInt(file.Fd(), unix.F_ADD_SEALS, unix.F_SEAL_WRITE|unix.F_SEAL_SHRINK|unix.F_SEAL_SEAL); err != nil {
		return nil, err
	}
	if _, err = file.Seek(0, io.SeekStart); err != nil {
		return nil, err
	}
	return file, nil
}

// Restore a sparse file, retaining holes for zero-filled chunks. Limit both the
// decompressed size and decoder memory before publishing a home to Kata.
func restoreImage(ctx context.Context, snapshot io.Reader, image string, size int64) error {
	source := &io.LimitedReader{R: contextReader{ctx, snapshot}, N: maxSnapshotSize(size) + 1}
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
		if source.N == 0 {
			return fmt.Errorf("compressed snapshot exceeds volume size")
		}
		return file.Truncate(total)
	})
}

func maxSnapshotSize(imageSize int64) int64 {
	return imageSize + imageSize/128 + (1 << 20)
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
