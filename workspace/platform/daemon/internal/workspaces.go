package daemon

import (
	"context"
	"errors"
	"net/http"
	"net/netip"
	"os"
	"path/filepath"
	"sort"
	"strings"

	dockercontainer "github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/mount"
	dockernetwork "github.com/docker/docker/api/types/network"
	"github.com/docker/docker/api/types/strslice"
	dockerclient "github.com/docker/docker/client"
	"github.com/google/uuid"
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

	active := ""
	if body.Volume != nil {
		active = s.activePath(body.Volume.VolumeUUID)
		if _, err := os.Stat(active); err != nil {
			jsonError(w, http.StatusNotFound, "active_not_found", "Active volume not found")
			return
		}
	}
	if _, err := s.docker.ImageInspect(r.Context(), body.RuntimeConfig.ContainerImageRef); err != nil {
		jsonError(w, http.StatusConflict, "image_not_available", "Image is not available locally")
		return
	}

	workspaceIP, err := s.ipam.allocate()
	if err != nil {
		jsonError(w, http.StatusConflict, "ip_exhausted", err.Error())
		return
	}
	releaseIP := true
	defer func() {
		if releaseIP {
			s.ipam.release(workspaceIP)
		}
	}()

	containerConfig, hostConfig, networkingConfig := s.workspaceContainerConfig(workspaceUUID, workspaceIP, body, active)
	created, err := s.docker.ContainerCreate(r.Context(), containerConfig, hostConfig, networkingConfig, nil, workspaceUUID)
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	if err := s.docker.ContainerStart(r.Context(), created.ID, dockercontainer.StartOptions{}); err != nil {
		_ = s.docker.ContainerRemove(context.Background(), created.ID, dockercontainer.RemoveOptions{Force: true})
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	if err := waitForAgent(r.Context(), workspaceIP, s.config.agentPort); err != nil {
		_ = s.docker.ContainerRemove(context.Background(), created.ID, dockercontainer.RemoveOptions{Force: true})
		jsonError(w, http.StatusBadGateway, "workspace_agent_unreachable", err.Error())
		return
	}
	releaseIP = false
	s.proxies.Store(workspaceUUID, workspaceIP)
	writeJSON(w, http.StatusOK, map[string]any{"workspace_uuid": workspaceUUID})
}

func (s *Server) workspaceContainerConfig(
	workspaceUUID string,
	workspaceIP netip.Addr,
	body workspaceStartRequest,
	activeVolumePath string,
) (*dockercontainer.Config, *dockercontainer.HostConfig, *dockernetwork.NetworkingConfig) {
	labels := map[string]string{workspaceLabel: workspaceUUID}
	if body.Volume != nil {
		labels[volumeLabel] = body.Volume.VolumeUUID
	}
	entrypoint := filepath.Join(s.config.workspacePath, "bin", "workspace-entrypoint")
	containerConfig := &dockercontainer.Config{
		Image:      body.RuntimeConfig.ContainerImageRef,
		User:       "0:0",
		Entrypoint: strslice.StrSlice{"/bin/sh", "-c", `exec "$0" "$@"`, entrypoint},
		Cmd:        strslice.StrSlice(body.RuntimeConfig.Entrypoint),
		Env:        environment(body.RuntimeConfig.Env),
		Labels:     labels,
	}

	mounts := []mount.Mount{
		{
			Type:     mount.TypeBind,
			Source:   s.config.nixStorePath,
			Target:   "/nix/store",
			ReadOnly: true,
		},
	}
	if body.Volume != nil {
		mounts = append(mounts, mount.Mount{
			Type:   mount.TypeBind,
			Source: activeVolumePath,
			Target: body.Volume.DstPath,
		})
	}
	hostConfig := &dockercontainer.HostConfig{
		AutoRemove:  true,
		Runtime:     kataRuntime,
		Mounts:      mounts,
		NetworkMode: dockercontainer.NetworkMode(s.config.dockerNetwork),
		CapAdd:      strslice.StrSlice{"SYS_PTRACE", "SYS_ADMIN", "NET_ADMIN"},
		Sysctls: map[string]string{
			"net.ipv4.ip_unprivileged_port_start": "1024",
		},
		Resources: dockercontainer.Resources{
			Devices: []dockercontainer.DeviceMapping{
				{PathOnHost: "/dev/kvm", PathInContainer: "/dev/kvm", CgroupPermissions: "rwm"},
				{PathOnHost: "/dev/net/tun", PathInContainer: "/dev/net/tun", CgroupPermissions: "rwm"},
			},
		},
	}
	networkingConfig := &dockernetwork.NetworkingConfig{
		EndpointsConfig: map[string]*dockernetwork.EndpointSettings{
			s.config.dockerNetwork: {
				IPAMConfig: &dockernetwork.EndpointIPAMConfig{IPv4Address: workspaceIP.String()},
			},
		},
	}
	return containerConfig, hostConfig, networkingConfig
}

func (s *Server) handleWorkspaceStop(w http.ResponseWriter, r *http.Request) {
	workspaceUUID := r.PathValue("workspaceUUID")
	if err := s.docker.ContainerStop(r.Context(), workspaceUUID, dockercontainer.StopOptions{}); err != nil && !dockerclient.IsErrNotFound(err) {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	value, ok := s.proxies.Load(workspaceUUID)
	s.proxies.Delete(workspaceUUID)
	if ok {
		s.ipam.release(value.(netip.Addr))
	}
	writeJSON(w, http.StatusOK, map[string]any{"workspace_uuid": workspaceUUID, "stopped": true})
}

func validateWorkspaceStart(body workspaceStartRequest, volumeStorageEnabled bool) error {
	if body.RuntimeConfig.ContainerImageRef == "" {
		return errors.New("container_image_ref is required")
	}
	if flag, ok := body.RuntimeConfig.Env["PWN_FLAG"]; !ok || flag == "" {
		return errors.New("runtime_config.env.PWN_FLAG is required")
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

func environment(values map[string]string) []string {
	names := make([]string, 0, len(values))
	for name := range values {
		names = append(names, name)
	}
	sort.Strings(names)
	env := make([]string, 0, len(names))
	for _, name := range names {
		env = append(env, name+"="+values[name])
	}
	return env
}
