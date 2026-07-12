package daemon

import (
	"context"
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
	VolumeUUID string `json:"volume_uuid"`
	DstPath    string `json:"dst_path"`
}

type workspaceStartRequest struct {
	RuntimeConfig runtimeConfig    `json:"runtime_config"`
	Volume        *workspaceVolume `json:"volume,omitempty"`
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

	existing, err := s.workspaceSandboxes(r.Context(), workspaceUUID)
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	if len(existing) > 0 {
		jsonError(w, http.StatusConflict, "workspace_exists", "Workspace already exists")
		return
	}

	active := ""
	if body.Volume != nil {
		active = s.activePath(body.Volume.VolumeUUID)
		if _, err := os.Stat(active); err != nil {
			jsonError(w, http.StatusNotFound, "active_not_found", "Active volume not found")
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
		jsonError(w, http.StatusConflict, "image_not_available", "Image is not available locally")
		return
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
	cleanup := true
	defer func() {
		if cleanup {
			_ = s.removeSandbox(context.Background(), sandbox.PodSandboxId)
		}
	}()

	created, err := s.runtime.CreateContainer(r.Context(), &runtimeapi.CreateContainerRequest{
		PodSandboxId:  sandbox.PodSandboxId,
		Config:        containerConfig,
		SandboxConfig: sandboxConfig,
	})
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
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

	cleanup = false
	s.proxies.Store(workspaceUUID, workspaceIP)
	writeJSON(w, http.StatusOK, map[string]any{"workspace_uuid": workspaceUUID})
}

func (s *Server) workspaceContainerConfig(
	workspaceUUID string,
	body workspaceStartRequest,
	activeVolumePath string,
) (*runtimeapi.PodSandboxConfig, *runtimeapi.ContainerConfig) {
	labels := map[string]string{workspaceLabel: workspaceUUID}
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
	sandboxes, err := s.workspaceSandboxes(r.Context(), workspaceUUID)
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	for _, sandbox := range sandboxes {
		if err := s.removeSandbox(r.Context(), sandbox.Id); err != nil {
			jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
			return
		}
	}
	s.proxies.Delete(workspaceUUID)
	writeJSON(w, http.StatusOK, map[string]any{"workspace_uuid": workspaceUUID, "stopped": true})
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
