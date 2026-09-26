package daemon

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"unsafe"

	btrfs "github.com/containerd/btrfs"
	"github.com/google/uuid"
	"github.com/klauspost/compress/zstd"
	runtimeapi "k8s.io/cri-api/pkg/apis/runtime/v1"
)

const (
	btrfsSuperMagic        = 0x9123683e
	btrfsSubvolReadonly    = 1 << 1
	btrfsIOCSubvolGetflags = 0x80089419
	btrfsIOCSubvolSetflags = 0x4008941a
	btrfsIOCSend           = 0x40489426
	statfsNosuid           = 0x2
)

type btrfsSendArgs struct {
	SendFd            int64
	CloneSourcesCount uint64
	CloneSources      uint64
	ParentRoot        uint64
	Flags             uint64
	Version           uint32
	Reserved          [28]byte
}

type volumeSnapshot struct {
	SnapshotUUID string `json:"snapshot_uuid"`
	DownloadURL  string `json:"download_url"`
}

type volumeExportRequest struct {
	StopWorkspaceUUID string `json:"stop_workspace_uuid,omitempty"`
	UploadURL         string `json:"upload_url"`
}

// Export is a handoff: stop, capture, retire the writable home, and upload.
// Retired homes are never selected by prepareVolume, even after a restart.
func (s *Server) handleVolumeExport(w http.ResponseWriter, r *http.Request) {
	volumeUUID, snapshotUUID := r.PathValue("volumeUUID"), r.PathValue("snapshotUUID")
	body, ok := decodeJSON[volumeExportRequest](w, r)
	if !ok {
		return
	}
	if !validUUID(snapshotUUID) || body.UploadURL == "" || (body.StopWorkspaceUUID != "" && !validUUID(body.StopWorkspaceUUID)) {
		jsonError(w, 400, "invalid_request", "Invalid export parameters")
		return
	}
	release, ok := s.lockResources(w, "workspaceUUID:"+body.StopWorkspaceUUID)
	if !ok {
		return
	}
	defer release()
	if err := s.exportVolume(r.Context(), volumeUUID, snapshotUUID, body); err != nil {
		jsonError(w, 500, "volume_export_failed", err.Error())
		return
	}
	writeJSON(w, 200, map[string]any{"snapshot_uuid": snapshotUUID})
}

func (s *Server) exportVolume(ctx context.Context, volumeUUID, snapshotUUID string, body volumeExportRequest) error {
	if err := s.ensureVolumeDirs(volumeUUID); err != nil {
		return err
	}
	root := s.volumeRoot(volumeUUID)
	if err := os.MkdirAll(filepath.Join(root, "exports"), 0700); err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Join(root, "retired"), 0700); err != nil {
		return err
	}
	// URLs can be refreshed without changing the identity of an export.
	if err := recordRequest(filepath.Join(root, "exports", snapshotUUID), body.StopWorkspaceUUID); err != nil {
		return err
	}
	retired := filepath.Join(root, "retired", snapshotUUID)
	if _, err := os.Stat(retired); os.IsNotExist(err) {
		if err := recordRequest(filepath.Join(root, ".exporting"), snapshotUUID); err != nil {
			return err
		}
		if body.StopWorkspaceUUID != "" {
			if err := s.stopWorkspace(ctx, body.StopWorkspaceUUID); err != nil {
				return err
			}
		}
		if err := s.requireVolumeDetached(ctx, volumeUUID); err != nil {
			return err
		}
		snapshot := s.snapshotPath(volumeUUID, snapshotUUID)
		if _, err := os.Stat(snapshot); os.IsNotExist(err) {
			if err := btrfs.SubvolSnapshot(snapshot, s.activePath(volumeUUID), true); err != nil {
				return err
			}
		} else if err != nil {
			return err
		}
		if err := os.Rename(s.activePath(volumeUUID), retired); err != nil {
			return err
		}
		if err := syncDirectory(root); err != nil {
			return err
		}
		if err := syncDirectory(filepath.Dir(retired)); err != nil {
			return err
		}
	} else if err != nil {
		return err
	}
	// A delayed retry must not clear a newer export or retire a newer active home.
	if pending, err := os.ReadFile(filepath.Join(root, ".exporting")); err == nil && string(pending) == snapshotUUID {
		if err := os.Remove(filepath.Join(root, ".exporting")); err != nil {
			return err
		}
		if err := syncDirectory(root); err != nil {
			return err
		}
	}
	return uploadSnapshot(ctx, s.snapshotPath(volumeUUID, snapshotUUID), body.UploadURL)
}

func (s *Server) prepareVolume(ctx context.Context, volume workspaceVolume) (string, error) {
	if err := s.ensureVolumeDirs(volume.VolumeUUID); err != nil {
		return "", err
	}
	root, active := s.volumeRoot(volume.VolumeUUID), s.activePath(volume.VolumeUUID)
	if _, err := os.Stat(filepath.Join(root, ".exporting")); err == nil {
		return "", fmt.Errorf("volume export is incomplete")
	} else if !os.IsNotExist(err) {
		return "", err
	}
	if _, err := os.Stat(active); err == nil {
		return active, nil
	} else if !os.IsNotExist(err) {
		return "", err
	}
	preparing := filepath.Join(root, ".preparing")
	if _, err := os.Stat(preparing); err == nil {
		if err := btrfs.SubvolDelete(preparing); err != nil {
			return "", err
		}
	}
	if volume.Snapshot != nil {
		if err := s.fetchSnapshot(ctx, volume.VolumeUUID, *volume.Snapshot); err != nil {
			return "", err
		}
		if err := btrfs.SubvolSnapshot(preparing, s.snapshotPath(volume.VolumeUUID, volume.Snapshot.SnapshotUUID), false); err != nil {
			return "", err
		}
	} else {
		if err := btrfs.SubvolCreate(preparing); err != nil {
			return "", err
		}
		if err := os.Chown(preparing, 1000, 1000); err != nil {
			return "", err
		}
	}
	if err := os.Rename(preparing, active); err != nil {
		return "", err
	}
	return active, syncDirectory(root)
}

func (s *Server) fetchSnapshot(ctx context.Context, volumeUUID string, source volumeSnapshot) error {
	snapshot := s.snapshotPath(volumeUUID, source.SnapshotUUID)
	if _, err := os.Stat(snapshot); err == nil {
		return nil
	} else if !os.IsNotExist(err) {
		return err
	}
	receiving := filepath.Join(s.volumeRoot(volumeUUID), "receiving", uuid.NewString())
	if err := os.MkdirAll(receiving, 0755); err != nil {
		return err
	}
	defer btrfsRemoveAll(receiving)
	if err := downloadSnapshot(ctx, source.DownloadURL, receiving); err != nil {
		return err
	}
	received := filepath.Join(receiving, source.SnapshotUUID)
	if err := btrfsSetSubvolumeReadonly(received, false); err != nil {
		return err
	}
	if err := os.Rename(received, snapshot); err != nil {
		return err
	}
	if err := btrfsSetSubvolumeReadonly(snapshot, true); err != nil {
		return err
	}
	return syncDirectory(filepath.Dir(snapshot))
}

func (s *Server) requireVolumeDetached(ctx context.Context, volumeUUID string) error {
	result, err := s.runtime.ListPodSandbox(ctx, &runtimeapi.ListPodSandboxRequest{Filter: &runtimeapi.PodSandboxFilter{LabelSelector: map[string]string{volumeLabel: volumeUUID}}})
	if err != nil {
		return err
	}
	if len(result.Items) != 0 {
		return fmt.Errorf("volume is attached to a workspace")
	}
	return nil
}

func (s *Server) handleVolumeDelete(w http.ResponseWriter, r *http.Request) {
	volumeUUID := r.PathValue("volumeUUID")
	if err := s.requireVolumeDetached(r.Context(), volumeUUID); err != nil {
		jsonError(w, 409, "volume_busy", err.Error())
		return
	}
	root := s.volumeRoot(volumeUUID)
	// Remove nested received subvolumes before their parent directories.
	if entries, err := os.ReadDir(filepath.Join(root, "receiving")); err == nil {
		for _, entry := range entries {
			if err := btrfsRemoveAll(filepath.Join(root, "receiving", entry.Name())); err != nil {
				jsonError(w, 500, "internal_error", err.Error())
				return
			}
		}
	}
	for _, path := range []string{filepath.Join(root, "snapshots"), filepath.Join(root, "retired"), root} {
		if err := btrfsRemoveAll(path); err != nil {
			jsonError(w, 500, "internal_error", err.Error())
			return
		}
	}
	writeJSON(w, 200, map[string]any{"volume_uuid": volumeUUID, "status": "deleted"})
}

func (s *Server) volumeRoot(volumeUUID string) string {
	return filepath.Join(s.config.volumeBasePath, volumeUUID)
}

func (s *Server) activePath(volumeUUID string) string {
	return filepath.Join(s.volumeRoot(volumeUUID), "active")
}

func (s *Server) snapshotPath(volumeUUID, snapshotUUID string) string {
	return filepath.Join(s.volumeRoot(volumeUUID), "snapshots", snapshotUUID)
}

func (s *Server) ensureVolumeDirs(volumeUUID string) error {
	root := s.volumeRoot(volumeUUID)
	if err := os.MkdirAll(filepath.Join(root, "snapshots"), 0o755); err != nil {
		return err
	}
	return os.MkdirAll(filepath.Join(root, "receiving"), 0o755)
}

func validUUID(value string) bool {
	_, err := uuid.Parse(value)
	return err == nil
}

func btrfsRemoveAll(root string) error {
	entries, err := os.ReadDir(root)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	for _, entry := range entries {
		if entry.IsDir() {
			_ = btrfs.SubvolDelete(filepath.Join(root, entry.Name()))
		}
	}
	return os.RemoveAll(root)
}

func btrfsSetSubvolumeReadonly(path string, readonly bool) error {
	file, err := os.Open(path)
	if err != nil {
		return err
	}
	defer file.Close()

	var flags uint64
	if _, _, errno := syscall.Syscall(syscall.SYS_IOCTL, file.Fd(), btrfsIOCSubvolGetflags, uintptr(unsafe.Pointer(&flags))); errno != 0 {
		return errno
	}
	if readonly {
		flags |= btrfsSubvolReadonly
	} else {
		flags &^= btrfsSubvolReadonly
	}
	if _, _, errno := syscall.Syscall(syscall.SYS_IOCTL, file.Fd(), btrfsIOCSubvolSetflags, uintptr(unsafe.Pointer(&flags))); errno != 0 {
		return errno
	}
	return nil
}

func btrfsSend(source string, output io.Writer) error {
	sourceFile, err := os.Open(source)
	if err != nil {
		return err
	}
	defer sourceFile.Close()

	reader, writer, err := os.Pipe()
	if err != nil {
		return err
	}
	copyDone := make(chan error, 1)
	go func() {
		_, copyErr := io.Copy(output, reader)
		closeErr := reader.Close()
		if copyErr != nil {
			copyDone <- copyErr
		} else {
			copyDone <- closeErr
		}
	}()

	args := btrfsSendArgs{SendFd: int64(writer.Fd())}
	_, _, errno := syscall.Syscall(syscall.SYS_IOCTL, sourceFile.Fd(), btrfsIOCSend, uintptr(unsafe.Pointer(&args)))
	closeErr := writer.Close()
	copyErr := <-copyDone
	if errno != 0 {
		return fmt.Errorf("btrfs send failed: %w", errno)
	}
	if closeErr != nil {
		return closeErr
	}
	return copyErr
}

func btrfsReceive(ctx context.Context, destination string, input io.Reader) error {
	var stderr bytes.Buffer
	cmd := exec.CommandContext(ctx, "btrfs", "receive", "--chroot", destination)
	cmd.Stdin = input
	cmd.Stdout = io.Discard
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		message := strings.TrimSpace(stderr.String())
		if message != "" {
			return fmt.Errorf("btrfs receive failed: %s", message)
		}
		return fmt.Errorf("btrfs receive failed: %w", err)
	}
	return nil
}

func assertBtrfsPath(path string) error {
	var statfs syscall.Statfs_t
	if err := syscall.Statfs(path, &statfs); err != nil {
		return err
	}
	if statfs.Type != btrfsSuperMagic {
		return fmt.Errorf("%s is not on btrfs", path)
	}
	if uint64(statfs.Flags)&statfsNosuid == 0 {
		return fmt.Errorf("%s must be mounted nosuid", path)
	}
	return nil
}

func uploadSnapshot(ctx context.Context, snapshot, url string) error {
	bodyReader, bodyWriter := io.Pipe()
	req, err := http.NewRequestWithContext(ctx, http.MethodPut, url, bodyReader)
	if err != nil {
		_ = bodyReader.CloseWithError(err)
		_ = bodyWriter.CloseWithError(err)
		return err
	}

	sendDone := make(chan error, 1)
	go func() {
		zstdWriter, err := zstd.NewWriter(bodyWriter)
		if err != nil {
			_ = bodyWriter.CloseWithError(err)
			sendDone <- err
			return
		}
		sendErr := btrfsSend(snapshot, zstdWriter)
		closeErr := zstdWriter.Close()
		if sendErr == nil {
			sendErr = closeErr
		}
		if sendErr != nil {
			_ = bodyWriter.CloseWithError(sendErr)
		} else {
			_ = bodyWriter.Close()
		}
		sendDone <- sendErr
	}()

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		_ = bodyReader.CloseWithError(err)
		sendErr := <-sendDone
		if sendErr != nil {
			return sendErr
		}
		return err
	}
	defer resp.Body.Close()
	responseBody, readErr := io.ReadAll(io.LimitReader(resp.Body, 4096))
	sendErr := <-sendDone
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return httpTransferStatusError(resp.StatusCode, responseBody)
	}
	if readErr != nil {
		return readErr
	}
	return sendErr
}

func downloadSnapshot(ctx context.Context, url, receiving string) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return err
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 4096))
		return httpTransferStatusError(resp.StatusCode, body)
	}
	zstdReader, err := zstd.NewReader(resp.Body)
	if err != nil {
		return err
	}
	defer zstdReader.Close()
	return btrfsReceive(ctx, receiving, zstdReader)
}

func httpTransferStatusError(statusCode int, body []byte) error {
	message := strings.TrimSpace(string(body))
	if message == "" {
		return fmt.Errorf("volume transfer failed with HTTP status %d", statusCode)
	}
	return fmt.Errorf("volume transfer failed with HTTP status %d: %s", statusCode, message)
}
