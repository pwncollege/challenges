package daemon

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/google/uuid"
	runtimeapi "k8s.io/cri-api/pkg/apis/runtime/v1"
)

type volumeSnapshot struct {
	SnapshotUUID string `json:"snapshot_uuid"`
	DownloadURL  string `json:"download_url"`
}

type volumeExportRequest struct {
	StopWorkspaceUUID string `json:"stop_workspace_uuid,omitempty"`
	UploadURL         string `json:"upload_url"`
}

// Export is a handoff: stop, retire the writable home, compress, and upload.
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
	// Only one compressed payload is resident per node, including while uploading.
	select {
	case s.snapshotUploads <- struct{}{}:
		defer func() { <-s.snapshotUploads }()
	case <-ctx.Done():
		return ctx.Err()
	}
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
		if err := unregisterVolume(ctx, s.activePath(volumeUUID)); err != nil {
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
	// The retired raw image survives failures and restarts. Retrying the same
	// snapshot recompresses these exact bytes without touching a newer home.
	snapshot, err := captureImage(ctx, filepath.Join(retired, "home.ext4"))
	if err != nil {
		return err
	}
	defer snapshot.Close()
	return uploadSnapshot(ctx, snapshot, body.UploadURL)
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
	if err := os.RemoveAll(preparing); err != nil {
		return "", err
	}
	if err := os.Mkdir(preparing, 0700); err != nil {
		return "", err
	}
	defer os.RemoveAll(preparing)
	image := filepath.Join(preparing, "home.ext4")
	if volume.Snapshot != nil {
		if err := downloadSnapshot(ctx, volume.Snapshot.DownloadURL, image, volume.MaxSizeBytes); err != nil {
			return "", err
		}
	} else if err := createImage(ctx, image, volume.MaxSizeBytes); err != nil {
		return "", err
	}
	if err := syncDirectory(preparing); err != nil {
		return "", err
	}
	if err := os.Rename(preparing, active); err != nil {
		return "", err
	}
	return active, syncDirectory(root)
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
	if err := unregisterVolume(r.Context(), s.activePath(volumeUUID)); err != nil {
		jsonError(w, 500, "internal_error", err.Error())
		return
	}
	if err := os.RemoveAll(s.volumeRoot(volumeUUID)); err != nil {
		jsonError(w, 500, "internal_error", err.Error())
		return
	}
	if err := syncDirectory(s.config.volumeBasePath); err != nil {
		jsonError(w, 500, "internal_error", err.Error())
		return
	}
	writeJSON(w, 200, map[string]any{"volume_uuid": volumeUUID, "status": "deleted"})
}

func (s *Server) volumeRoot(volumeUUID string) string {
	return filepath.Join(s.config.volumeBasePath, volumeUUID)
}

func (s *Server) activePath(volumeUUID string) string {
	return filepath.Join(s.volumeRoot(volumeUUID), "active")
}

func (s *Server) ensureVolumeDirs(volumeUUID string) error {
	root := s.volumeRoot(volumeUUID)
	if err := os.MkdirAll(root, 0700); err != nil {
		return err
	}
	if err := syncDirectory(root); err != nil {
		return err
	}
	return syncDirectory(s.config.volumeBasePath)
}

func validUUID(value string) bool {
	_, err := uuid.Parse(value)
	return err == nil
}

// Capturing first gives every upload a known length and immutable retry data.
func uploadSnapshot(ctx context.Context, file *os.File, url string) error {
	info, err := file.Stat()
	if err != nil {
		return err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPut, url, file)
	if err != nil {
		return err
	}
	req.ContentLength = info.Size()
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(io.LimitReader(resp.Body, 4096))
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return httpTransferStatusError(resp.StatusCode, body)
	}
	return err
}

func downloadSnapshot(ctx context.Context, url, destination string, maxImageSize int64) error {
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
	if resp.ContentLength > maxSnapshotSize(maxImageSize) {
		return fmt.Errorf("snapshot exceeds volume size")
	}
	return restoreImage(ctx, resp.Body, destination, maxImageSize)
}

func httpTransferStatusError(statusCode int, body []byte) error {
	message := strings.TrimSpace(string(body))
	if message == "" {
		return fmt.Errorf("volume transfer failed with HTTP status %d", statusCode)
	}
	return fmt.Errorf("volume transfer failed with HTTP status %d: %s", statusCode, message)
}
