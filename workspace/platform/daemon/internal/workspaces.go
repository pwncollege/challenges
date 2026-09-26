package daemon

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/google/uuid"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	runtimeapi "k8s.io/cri-api/pkg/apis/runtime/v1"
)

type runtimeConfig struct {
	ContainerImageRef string            `json:"container_image_ref"`
	Entrypoint        []string          `json:"entrypoint,omitempty"`
	Env               map[string]string `json:"env,omitempty"`
}

type workspaceVolume struct {
	VolumeUUID   string          `json:"volume_uuid"`
	DstPath      string          `json:"dst_path"`
	MaxSizeBytes int64           `json:"max_size_bytes"`
	Snapshot     *volumeSnapshot `json:"snapshot"`
}

type workspaceStartRequest struct {
	ReplaceWorkspaceUUID string           `json:"replace_workspace_uuid,omitempty"`
	RuntimeConfig        runtimeConfig    `json:"runtime_config"`
	Volume               *workspaceVolume `json:"volume,omitempty"`
}

func (s *Server) handleWorkspaceStart(w http.ResponseWriter, r *http.Request) {
	workspaceUUID := r.PathValue("workspaceUUID")
	body, ok := decodeJSON[workspaceStartRequest](w, r)
	if !ok {
		return
	}
	if err := validateWorkspaceStart(body, s.config.volumeBasePath != ""); err != nil {
		jsonError(w, http.StatusBadRequest, "invalid_request", err.Error())
		return
	}

	keys := []string{"workspaceUUID:" + body.ReplaceWorkspaceUUID}
	if body.ReplaceWorkspaceUUID == workspaceUUID {
		jsonError(w, 400, "invalid_request", "Cannot replace the workspace being started")
		return
	}
	if body.Volume != nil {
		keys = append(keys, "volumeUUID:"+body.Volume.VolumeUUID)
	}
	release, ok := s.lockResources(w, keys...)
	if !ok {
		return
	}
	defer release()
	requestPath := filepath.Join(s.config.logDirectory, workspaceUUID, ".request")
	if previous, err := os.ReadFile(requestPath); err == nil && string(previous) != startRequestHash(body) {
		jsonError(w, 409, "workspace_request_conflict", "Workspace UUID has different start parameters")
		return
	} else if err != nil && !os.IsNotExist(err) {
		jsonError(w, 500, "internal_error", err.Error())
		return
	}

	// Workspace UUIDs identify one lifetime. A delayed start must not undo a stop.
	if _, err := os.Stat(s.workspaceStoppedPath(workspaceUUID)); err == nil {
		jsonError(w, http.StatusConflict, "workspace_stopped", "Workspace has been stopped")
		return
	} else if !os.IsNotExist(err) {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}

	existing, err := s.workspaceSandboxes(r.Context(), workspaceUUID)
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	if len(existing) > 1 {
		jsonError(w, http.StatusConflict, "workspace_request_conflict", "Workspace has multiple sandboxes")
		return
	}
	for _, sandbox := range existing {
		if sandbox.Labels[startRequestLabel] != startRequestHash(body) {
			jsonError(w, http.StatusConflict, "workspace_request_conflict", "Workspace UUID has different start parameters")
			return
		}
		containers, err := s.runtime.ListContainers(r.Context(), &runtimeapi.ListContainersRequest{
			Filter: &runtimeapi.ContainerFilter{PodSandboxId: sandbox.Id},
		})
		if err != nil {
			jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
			return
		}
		for _, container := range containers.Containers {
			if container.State == runtimeapi.ContainerState_CONTAINER_EXITED {
				jsonError(w, http.StatusConflict, "workspace_exited", "Workspace container has exited")
				return
			}
		}
		if sandbox.State == runtimeapi.PodSandboxState_SANDBOX_READY &&
			len(containers.Containers) == 1 && containers.Containers[0].State == runtimeapi.ContainerState_CONTAINER_RUNNING {
			ip, err := s.sandboxIP(r.Context(), sandbox.Id)
			if err == nil {
				err = waitForAgent(r.Context(), ip, s.config.agentPort)
			}
			if err != nil {
				jsonError(w, http.StatusBadGateway, "workspace_agent_unreachable", err.Error())
				return
			}
			s.proxies.Store(workspaceUUID, ip)
			writeJSON(w, http.StatusOK, map[string]any{"workspace_uuid": workspaceUUID})
			return
		}
		if _, err := os.Stat(filepath.Join(s.config.logDirectory, workspaceUUID, ".launched")); err == nil {
			jsonError(w, 409, "workspace_start_incomplete", "Workspace launch needs reconciliation")
			return
		}
		// A daemon restart may leave an incomplete matching sandbox.
		if err := s.removeSandbox(r.Context(), sandbox.Id); err != nil {
			jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
			return
		}
	}

	image, err := s.images.ImageStatus(r.Context(), &runtimeapi.ImageStatusRequest{
		Image: &runtimeapi.ImageSpec{Image: body.RuntimeConfig.ContainerImageRef},
	})
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	if image.Image == nil {
		writeJSON(w, http.StatusConflict, map[string]any{"operation_started": func() bool { _, err := os.Stat(requestPath); return !os.IsNotExist(err) }(), "error": map[string]any{"code": "image_not_available", "message": "Image is not available locally"}})
		return
	}

	if _, err := os.Stat(filepath.Join(s.config.logDirectory, workspaceUUID, ".launched")); err == nil {
		jsonError(w, 409, "workspace_start_incomplete", "Workspace launch needs reconciliation")
		return
	} else if !os.IsNotExist(err) {
		jsonError(w, 500, "internal_error", err.Error())
		return
	}
	if err := recordRequest(requestPath, startRequestHash(body)); err != nil {
		jsonError(w, 409, "workspace_request_conflict", err.Error())
		return
	}
	if body.ReplaceWorkspaceUUID != "" {
		if err := s.stopWorkspace(r.Context(), body.ReplaceWorkspaceUUID); err != nil {
			jsonError(w, 500, "workspace_stop_failed", err.Error())
			return
		}
	}
	active := ""
	if body.Volume != nil {
		if err := s.requireVolumeDetached(r.Context(), body.Volume.VolumeUUID); err != nil {
			jsonError(w, 409, "volume_busy", err.Error())
			return
		}
		active, err = s.prepareVolume(r.Context(), *body.Volume)
		if err != nil {
			jsonError(w, 500, "volume_prepare_failed", err.Error())
			return
		}
	}

	sandboxConfig, containerConfig := s.workspaceContainerConfig(workspaceUUID, body, active)
	if err := os.MkdirAll(sandboxConfig.LogDirectory, 0o711); err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	sandbox, err := s.runtime.RunPodSandbox(r.Context(), &runtimeapi.RunPodSandboxRequest{
		Config:         sandboxConfig,
		RuntimeHandler: kataRuntime,
	})
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	created, err := s.runtime.CreateContainer(r.Context(), &runtimeapi.CreateContainerRequest{
		PodSandboxId:  sandbox.PodSandboxId,
		Config:        containerConfig,
		SandboxConfig: sandboxConfig,
	})
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	if err := recordRequest(filepath.Join(s.config.logDirectory, workspaceUUID, ".launched"), ""); err != nil {
		jsonError(w, 500, "internal_error", err.Error())
		return
	}
	if _, err := s.runtime.StartContainer(r.Context(), &runtimeapi.StartContainerRequest{ContainerId: created.ContainerId}); err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	workspaceIP, err := s.sandboxIP(r.Context(), sandbox.PodSandboxId)
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	if err := waitForAgent(r.Context(), workspaceIP, s.config.agentPort); err != nil {
		jsonError(w, http.StatusBadGateway, "workspace_agent_unreachable", err.Error())
		return
	}

	s.proxies.Store(workspaceUUID, workspaceIP)
	writeJSON(w, http.StatusOK, map[string]any{"workspace_uuid": workspaceUUID})
}

func (s *Server) workspaceContainerConfig(
	workspaceUUID string,
	body workspaceStartRequest,
	activeVolumePath string,
) (*runtimeapi.PodSandboxConfig, *runtimeapi.ContainerConfig) {
	labels := map[string]string{workspaceLabel: workspaceUUID, startRequestLabel: startRequestHash(body)}
	if body.Volume != nil {
		labels[volumeLabel] = body.Volume.VolumeUUID
	}
	sandbox := &runtimeapi.PodSandboxConfig{
		Metadata: &runtimeapi.PodSandboxMetadata{
			Name:      workspaceUUID,
			Uid:       workspaceUUID,
			Namespace: "pwn-workspaces",
		},
		Hostname:     workspaceUUID,
		LogDirectory: filepath.Join(s.config.logDirectory, workspaceUUID),
		Labels:       labels,
		Linux: &runtimeapi.LinuxPodSandboxConfig{
			Sysctls: map[string]string{
				"net.ipv4.ip_unprivileged_port_start": "1024",
			},
		},
		DnsConfig: &runtimeapi.DNSConfig{Servers: []string{s.config.egressAddress}},
	}

	entrypoint := filepath.Join(s.config.workspacePath, "bin", "workspace-entrypoint")
	mounts := []*runtimeapi.Mount{
		{
			HostPath:      s.config.nixStorePath,
			ContainerPath: "/nix/store",
			Readonly:      true,
		},
	}
	if body.Volume != nil {
		mounts = append(mounts, &runtimeapi.Mount{
			HostPath:      activeVolumePath,
			ContainerPath: body.Volume.DstPath,
		})
	}
	container := &runtimeapi.ContainerConfig{
		Metadata: &runtimeapi.ContainerMetadata{Name: "workspace"},
		Image: &runtimeapi.ImageSpec{
			Image:          body.RuntimeConfig.ContainerImageRef,
			RuntimeHandler: kataRuntime,
		},
		Command: []string{"/bin/sh", "-c", `exec "$0" "$@"`, entrypoint},
		Args:    body.RuntimeConfig.Entrypoint,
		Envs:    environment(body.RuntimeConfig.Env),
		Mounts:  mounts,
		Devices: []*runtimeapi.Device{
			{HostPath: "/dev/kvm", ContainerPath: "/dev/kvm", Permissions: "rwm"},
			{HostPath: "/dev/net/tun", ContainerPath: "/dev/net/tun", Permissions: "rwm"},
		},
		Labels:  labels,
		LogPath: "workspace.log",
		Linux: &runtimeapi.LinuxContainerConfig{
			SecurityContext: &runtimeapi.LinuxContainerSecurityContext{
				RunAsUser:  &runtimeapi.Int64Value{Value: 0},
				RunAsGroup: &runtimeapi.Int64Value{Value: 0},
				Capabilities: &runtimeapi.Capability{
					AddCapabilities: []string{"SYS_PTRACE", "SYS_ADMIN", "NET_ADMIN"},
				},
				Seccomp: &runtimeapi.SecurityProfile{
					ProfileType:  runtimeapi.SecurityProfile_Localhost,
					LocalhostRef: s.config.seccompProfile,
				},
			},
		},
	}
	return sandbox, container
}

func (s *Server) handleWorkspaceStop(w http.ResponseWriter, r *http.Request) {
	workspaceUUID := r.PathValue("workspaceUUID")
	if err := s.stopWorkspace(r.Context(), workspaceUUID); err != nil {
		jsonError(w, 500, "workspace_stop_failed", err.Error())
		return
	}
	writeJSON(w, 200, map[string]any{"workspace_uuid": workspaceUUID, "stopped": true})
}

func (s *Server) stopWorkspace(ctx context.Context, workspaceUUID string) error {
	if err := recordRequest(s.workspaceStoppedPath(workspaceUUID), ""); err != nil {
		return err
	}
	sandboxes, err := s.workspaceSandboxes(ctx, workspaceUUID)
	if err != nil {
		return err
	}
	for _, sandbox := range sandboxes {
		if err := s.removeSandbox(ctx, sandbox.Id); err != nil {
			return err
		}
	}
	s.proxies.Delete(workspaceUUID)
	return nil
}

func (s *Server) removeSandbox(ctx context.Context, sandboxID string) error {
	response, err := s.runtime.ListContainers(ctx, &runtimeapi.ListContainersRequest{
		Filter: &runtimeapi.ContainerFilter{PodSandboxId: sandboxID},
	})
	if err != nil && status.Code(err) != codes.NotFound {
		return err
	}
	for _, container := range response.GetContainers() {
		_, stopErr := s.runtime.StopContainer(ctx, &runtimeapi.StopContainerRequest{
			ContainerId: container.Id,
			Timeout:     10,
		})
		if stopErr != nil && status.Code(stopErr) != codes.NotFound {
			return stopErr
		}
		if _, err := s.runtime.RemoveContainer(ctx, &runtimeapi.RemoveContainerRequest{ContainerId: container.Id}); err != nil && status.Code(err) != codes.NotFound {
			return err
		}
	}
	if _, err := s.runtime.StopPodSandbox(ctx, &runtimeapi.StopPodSandboxRequest{PodSandboxId: sandboxID}); err != nil && status.Code(err) != codes.NotFound {
		return err
	}
	if _, err := s.runtime.RemovePodSandbox(ctx, &runtimeapi.RemovePodSandboxRequest{PodSandboxId: sandboxID}); err != nil && status.Code(err) != codes.NotFound {
		return err
	}
	return nil
}

func validateWorkspaceStart(body workspaceStartRequest, volumeStorageEnabled bool) error {
	if body.ReplaceWorkspaceUUID != "" && !validUUID(body.ReplaceWorkspaceUUID) {
		return errors.New("replace_workspace_uuid must be a UUID")
	}
	if body.RuntimeConfig.ContainerImageRef == "" {
		return errors.New("container_image_ref is required")
	}
	for name, value := range body.RuntimeConfig.Env {
		if name == "" || strings.ContainsAny(name, "=\x00") || strings.ContainsRune(value, '\x00') {
			return errors.New("runtime_config.env contains an invalid environment variable")
		}
	}
	if len(body.RuntimeConfig.Entrypoint) > 0 && body.RuntimeConfig.Entrypoint[0] == "" {
		return errors.New("runtime_config.entrypoint must start with a non-empty executable")
	}
	if body.Volume == nil {
		return nil
	}
	if !volumeStorageEnabled {
		return errors.New("volume storage is not configured")
	}
	if _, err := uuid.Parse(body.Volume.VolumeUUID); err != nil {
		return errors.New("volume.volume_uuid must be a UUID")
	}
	if body.Volume.MaxSizeBytes < 64*1024*1024 || body.Volume.MaxSizeBytes%4096 != 0 {
		return errors.New("volume.max_size_bytes must be a multiple of 4096 and at least 64 MiB")
	}
	if source := body.Volume.Snapshot; source != nil && (!validUUID(source.SnapshotUUID) || source.DownloadURL == "") {
		return errors.New("volume.snapshot requires a UUID and download URL")
	}
	if err := validateVolumeDestination(body.Volume.DstPath); err != nil {
		return err
	}
	return nil
}

func validateVolumeDestination(path string) error {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path || path == "/" {
		return errors.New("volume.dst_path must be an absolute normalized path other than /")
	}
	reserved := []string{"/bin", "/boot", "/dev", "/etc", "/nix", "/proc", "/run", "/sbin", "/sys", "/usr", "/var"}
	for _, prefix := range reserved {
		if path == prefix || strings.HasPrefix(path, prefix+"/") {
			return errors.New("volume.dst_path targets a reserved path")
		}
	}
	return nil
}

func environment(values map[string]string) []*runtimeapi.KeyValue {
	names := make([]string, 0, len(values))
	for name := range values {
		names = append(names, name)
	}
	sort.Strings(names)
	env := make([]*runtimeapi.KeyValue, 0, len(names))
	for _, name := range names {
		env = append(env, &runtimeapi.KeyValue{Key: name, Value: values[name]})
	}
	return env
}

const startRequestLabel = "pwn.start-request-sha256"

func startRequestHash(body workspaceStartRequest) string {
	if body.Volume != nil && body.Volume.Snapshot != nil {
		volume, snapshot := *body.Volume, *body.Volume.Snapshot
		snapshot.DownloadURL = ""
		volume.Snapshot = &snapshot
		body.Volume = &volume
	}
	data, _ := json.Marshal(body)
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:])
}

func (s *Server) workspaceStoppedPath(workspaceUUID string) string {
	return filepath.Join(s.config.logDirectory, workspaceUUID, ".stopped")
}
