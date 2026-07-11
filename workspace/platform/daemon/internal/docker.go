package daemon

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"net/netip"

	cerrdefs "github.com/containerd/errdefs"
	dockercontainer "github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/filters"
	dockerimage "github.com/docker/docker/api/types/image"
	dockernetwork "github.com/docker/docker/api/types/network"
)

const (
	workspaceLabel        = "pwn.workspace-uuid"
	volumeLabel           = "pwn.volume-uuid"
	workspaceNetworkLabel = "pwn.workspace-network"
	kataRuntime           = "kata"
)

type containerImageRequest struct {
	ContainerImageRef string `json:"container_image_ref"`
}

func (s *Server) handleImageList(w http.ResponseWriter, r *http.Request) {
	list, err := s.docker.ImageList(r.Context(), dockerimage.ListOptions{})
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	images := []map[string]any{}
	for _, row := range list {
		images = append(images, map[string]any{
			"repo_tags":    row.RepoTags,
			"repo_digests": row.RepoDigests,
			"image_id":     row.ID,
		})
	}
	writeJSON(w, http.StatusOK, map[string]any{"images": images})
}

func (s *Server) handleImagePull(w http.ResponseWriter, r *http.Request) {
	body, ok := decodeJSON[containerImageRequest](w, r)
	if !ok {
		return
	}
	if body.ContainerImageRef == "" {
		jsonError(w, http.StatusBadRequest, "invalid_request", "container_image_ref is required")
		return
	}
	pulled, err := s.docker.ImagePull(r.Context(), body.ContainerImageRef, dockerimage.PullOptions{})
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	_, _ = io.Copy(io.Discard, pulled)
	_ = pulled.Close()
	writeJSON(w, http.StatusOK, map[string]any{"container_image_ref": body.ContainerImageRef, "pulled": true})
}

func (s *Server) handleImageRemove(w http.ResponseWriter, r *http.Request) {
	body, ok := decodeJSON[containerImageRequest](w, r)
	if !ok {
		return
	}
	if body.ContainerImageRef == "" {
		jsonError(w, http.StatusBadRequest, "invalid_request", "container_image_ref is required")
		return
	}
	if _, err := s.docker.ImageRemove(r.Context(), body.ContainerImageRef, dockerimage.RemoveOptions{}); err != nil {
		if cerrdefs.IsNotFound(err) {
			jsonError(w, http.StatusNotFound, "image_not_found", err.Error())
			return
		}
		if cerrdefs.IsConflict(err) {
			jsonError(w, http.StatusConflict, "image_in_use", err.Error())
			return
		}
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"container_image_ref": body.ContainerImageRef, "removed": true})
}

func (s *Server) validateWorkspaceNetwork(ctx context.Context) error {
	_, _, err := s.workspaceNetworkConfig(ctx)
	return err
}

func (s *Server) workspaceNetworkConfig(ctx context.Context) (netip.Prefix, []netip.Addr, error) {
	network, err := s.docker.NetworkInspect(ctx, s.config.dockerNetwork, dockernetwork.InspectOptions{})
	if err != nil {
		return netip.Prefix{}, nil, fmt.Errorf("inspect workspace network: %w", err)
	}
	if network.Driver != "bridge" {
		return netip.Prefix{}, nil, fmt.Errorf("workspace network %s uses driver %s, not bridge", s.config.dockerNetwork, network.Driver)
	}
	if network.Labels[workspaceNetworkLabel] != "true" {
		return netip.Prefix{}, nil, fmt.Errorf("workspace network %s is not reserved for workspaces", s.config.dockerNetwork)
	}

	var subnet netip.Prefix
	var reservedAddresses []netip.Addr
	for _, networkConfig := range network.IPAM.Config {
		prefix, err := netip.ParsePrefix(networkConfig.Subnet)
		if err != nil {
			return netip.Prefix{}, nil, fmt.Errorf("workspace network %s has invalid subnet %q: %w", s.config.dockerNetwork, networkConfig.Subnet, err)
		}
		if !prefix.Addr().Is4() {
			continue
		}
		if subnet.IsValid() {
			return netip.Prefix{}, nil, fmt.Errorf("workspace network %s must have exactly one IPv4 subnet", s.config.dockerNetwork)
		}
		subnet = prefix.Masked()
		addresses := make([]string, 0, len(networkConfig.AuxAddress)+1)
		if networkConfig.Gateway != "" {
			addresses = append(addresses, networkConfig.Gateway)
		}
		for _, address := range networkConfig.AuxAddress {
			addresses = append(addresses, address)
		}
		for _, value := range addresses {
			address, err := netip.ParseAddr(value)
			if err != nil || !subnet.Contains(address) {
				return netip.Prefix{}, nil, fmt.Errorf("workspace network %s has invalid reserved address %q", s.config.dockerNetwork, value)
			}
			reservedAddresses = append(reservedAddresses, address)
		}
	}
	if !subnet.IsValid() {
		return netip.Prefix{}, nil, fmt.Errorf("workspace network %s has no IPv4 subnet", s.config.dockerNetwork)
	}
	return subnet, reservedAddresses, nil
}

func (s *Server) rebuildProxyState(ctx context.Context) error {
	network, err := s.docker.NetworkInspect(ctx, s.config.dockerNetwork, dockernetwork.InspectOptions{})
	if err != nil {
		return err
	}
	for _, endpoint := range network.Containers {
		prefix, err := netip.ParsePrefix(endpoint.IPv4Address)
		if err != nil {
			return err
		}
		if err := s.ipam.reserve(prefix.Addr()); err != nil {
			return err
		}
	}

	containers, err := s.docker.ContainerList(ctx, dockercontainer.ListOptions{
		Filters: filters.NewArgs(filters.Arg("label", workspaceLabel)),
	})
	if err != nil {
		return err
	}
	for _, container := range containers {
		workspaceUUID := container.Labels[workspaceLabel]
		if container.NetworkSettings == nil {
			continue
		}
		endpoint := container.NetworkSettings.Networks[s.config.dockerNetwork]
		if endpoint == nil || endpoint.IPAddress == "" {
			continue
		}
		ip, err := netip.ParseAddr(endpoint.IPAddress)
		if err != nil {
			return err
		}
		s.proxies.Store(workspaceUUID, ip)
	}
	return nil
}
