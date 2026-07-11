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

type volumeActivateRequest struct {
	SnapshotUUID *string `json:"snapshot_uuid"`
}

type volumeSnapshotRequest struct {
	SnapshotUUID string `json:"snapshot_uuid"`
}

type volumeTransferRequest struct {
	SnapshotUUID string `json:"snapshot_uuid"`
	URL          string `json:"url"`
}

func (s *Server) handleVolumeActivate(w http.ResponseWriter, r *http.Request) {
	volumeUUID := r.PathValue("volumeUUID")
	body, ok := decodeJSON[volumeActivateRequest](w, r)
	if !ok {
		return
	}
	if body.SnapshotUUID != nil && !validUUID(*body.SnapshotUUID) {
		jsonError(w, http.StatusBadRequest, "invalid_request", "Invalid snapshot UUID")
		return
	}

	if err := s.ensureVolumeDirs(volumeUUID); err != nil {
		jsonError(w, http.StatusBadRequest, "invalid_request", err.Error())
		return
	}
	active := s.activePath(volumeUUID)
	if _, err := os.Stat(active); err == nil {
		jsonError(w, http.StatusConflict, "active_exists", "Active volume exists")
		return
	}
	if body.SnapshotUUID != nil {
		if err := btrfs.SubvolSnapshot(active, s.snapshotPath(volumeUUID, *body.SnapshotUUID), false); err != nil {
			jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
			return
		}
	} else if err := btrfs.SubvolCreate(active); err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	} else if err := os.Chown(active, 1000, 1000); err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"volume_uuid": volumeUUID, "snapshot_uuid": body.SnapshotUUID, "status": "activated"})
}

func (s *Server) handleVolumeDeactivate(w http.ResponseWriter, r *http.Request) {
	volumeUUID := r.PathValue("volumeUUID")

	active := s.activePath(volumeUUID)
	if _, err := os.Stat(active); os.IsNotExist(err) {
		writeJSON(w, http.StatusOK, map[string]any{"volume_uuid": volumeUUID, "status": "deactivated"})
		return
	} else if err != nil {
		jsonError(w, http.StatusConflict, "active_busy", err.Error())
		return
	}
	if err := btrfs.SubvolDelete(active); err != nil {
		jsonError(w, http.StatusConflict, "active_busy", err.Error())
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"volume_uuid": volumeUUID, "status": "deactivated"})
}

func (s *Server) handleVolumeSnapshot(w http.ResponseWriter, r *http.Request) {
	volumeUUID := r.PathValue("volumeUUID")
	body, ok := decodeJSON[volumeSnapshotRequest](w, r)
	if !ok {
		return
	}
	if !validUUID(body.SnapshotUUID) {
		jsonError(w, http.StatusBadRequest, "invalid_request", "Invalid snapshot UUID")
		return
	}

	if err := s.ensureVolumeDirs(volumeUUID); err != nil {
		jsonError(w, http.StatusBadRequest, "invalid_request", err.Error())
		return
	}
	active := s.activePath(volumeUUID)
	snapshot := s.snapshotPath(volumeUUID, body.SnapshotUUID)
	if _, err := os.Stat(active); err != nil {
		jsonError(w, http.StatusNotFound, "active_not_found", "Active volume not found")
		return
	}
	if _, err := os.Stat(snapshot); err == nil {
		writeJSON(w, http.StatusOK, map[string]any{"volume_uuid": volumeUUID, "snapshot_uuid": body.SnapshotUUID, "status": "exists"})
		return
	}
	if err := btrfs.SubvolSnapshot(snapshot, active, true); err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"volume_uuid": volumeUUID, "snapshot_uuid": body.SnapshotUUID, "status": "created"})
}

func (s *Server) handleVolumeUpload(w http.ResponseWriter, r *http.Request) {
	volumeUUID := r.PathValue("volumeUUID")
	body, ok := decodeJSON[volumeTransferRequest](w, r)
	if !ok {
		return
	}
	if !validUUID(body.SnapshotUUID) || body.URL == "" {
		jsonError(w, http.StatusBadRequest, "invalid_request", "Snapshot UUID and URL are required")
		return
	}

	snapshot := s.snapshotPath(volumeUUID, body.SnapshotUUID)
	if _, err := os.Stat(snapshot); err != nil {
		jsonError(w, http.StatusNotFound, "snapshot_not_found", "Snapshot not found")
		return
	}
	if err := uploadSnapshot(r.Context(), snapshot, body.URL); err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"volume_uuid": volumeUUID, "snapshot_uuid": body.SnapshotUUID, "status": "uploaded"})
}

func (s *Server) handleVolumeDownload(w http.ResponseWriter, r *http.Request) {
	volumeUUID := r.PathValue("volumeUUID")
	body, ok := decodeJSON[volumeTransferRequest](w, r)
	if !ok {
		return
	}
	if !validUUID(body.SnapshotUUID) || body.URL == "" {
		jsonError(w, http.StatusBadRequest, "invalid_request", "Snapshot UUID and URL are required")
		return
	}

	if err := s.ensureVolumeDirs(volumeUUID); err != nil {
		jsonError(w, http.StatusBadRequest, "invalid_request", err.Error())
		return
	}
	snapshot := s.snapshotPath(volumeUUID, body.SnapshotUUID)
	if _, err := os.Stat(snapshot); err == nil {
		writeJSON(w, http.StatusOK, map[string]any{"volume_uuid": volumeUUID, "snapshot_uuid": body.SnapshotUUID, "status": "exists"})
		return
	}
	receiving := filepath.Join(s.volumeRoot(volumeUUID), "receiving", uuid.NewString())
	if err := os.MkdirAll(receiving, 0o755); err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	failReceive := func(subvolume string, err error) {
		if subvolume != "" {
			_ = btrfs.SubvolDelete(subvolume)
		}
		_ = btrfsRemoveAll(receiving)
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
	}
	if err := downloadSnapshot(r.Context(), body.URL, receiving); err != nil {
		failReceive("", err)
		return
	}
	received := filepath.Join(receiving, body.SnapshotUUID)
	if _, err := os.Stat(received); err != nil {
		failReceive("", err)
		return
	}
	if err := btrfsSetSubvolumeReadonly(received, false); err != nil {
		failReceive(received, err)
		return
	}
	if err := os.Rename(received, snapshot); err != nil {
		failReceive(received, err)
		return
	}
	if err := btrfsSetSubvolumeReadonly(snapshot, true); err != nil {
		failReceive(snapshot, err)
		return
	}
	_ = btrfsRemoveAll(receiving)
	writeJSON(w, http.StatusOK, map[string]any{"volume_uuid": volumeUUID, "snapshot_uuid": body.SnapshotUUID, "status": "downloaded"})
}

func (s *Server) handleVolumeDelete(w http.ResponseWriter, r *http.Request) {
	volumeUUID := r.PathValue("volumeUUID")

	root := s.volumeRoot(volumeUUID)
	if _, err := os.Stat(root); err == nil {
		receivingRoot := filepath.Join(root, "receiving")
		if entries, err := os.ReadDir(receivingRoot); err == nil {
			for _, entry := range entries {
				if entry.IsDir() {
					_ = btrfsRemoveAll(filepath.Join(receivingRoot, entry.Name()))
				}
			}
		}
		_ = btrfsRemoveAll(receivingRoot)
		_ = btrfsRemoveAll(filepath.Join(root, "snapshots"))
		_ = btrfs.SubvolDelete(s.activePath(volumeUUID))
		_ = os.RemoveAll(root)
	}
	writeJSON(w, http.StatusOK, map[string]any{"volume_uuid": volumeUUID, "status": "deleted"})
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

func (s *Server) withVolumeLock(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		volumeUUID := r.PathValue("volumeUUID")

		s.volumeLocksMu.Lock()
		if _, locked := s.volumeLocks[volumeUUID]; locked {
			s.volumeLocksMu.Unlock()
			w.Header().Set("Retry-After", "5")
			jsonError(w, http.StatusLocked, "volume_locked", "Volume is locked")
			return
		}
		s.volumeLocks[volumeUUID] = struct{}{}
		s.volumeLocksMu.Unlock()

		defer func() {
			s.volumeLocksMu.Lock()
			defer s.volumeLocksMu.Unlock()
			delete(s.volumeLocks, volumeUUID)
		}()
		next.ServeHTTP(w, r)
	})
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
