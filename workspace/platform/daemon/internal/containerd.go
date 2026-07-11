package daemon

import (
	"context"
	"fmt"
	"net/http"
	"net/netip"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	runtimeapi "k8s.io/cri-api/pkg/apis/runtime/v1"
)

const (
	workspaceLabel = "pwn.workspace-uuid"
	volumeLabel    = "pwn.volume-uuid"
	kataRuntime    = "kata"
)

type containerImageRequest struct {
	ContainerImageRef string `json:"container_image_ref"`
}

func (s *Server) handleImageList(w http.ResponseWriter, r *http.Request) {
	response, err := s.images.ListImages(r.Context(), &runtimeapi.ListImagesRequest{})
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	images := make([]map[string]any, 0, len(response.Images))
	for _, image := range response.Images {
		images = append(images, map[string]any{
			"repo_tags":    image.RepoTags,
			"repo_digests": image.RepoDigests,
			"image_id":     image.Id,
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
	response, err := s.images.PullImage(r.Context(), &runtimeapi.PullImageRequest{
		Image: &runtimeapi.ImageSpec{Image: body.ContainerImageRef, RuntimeHandler: kataRuntime},
	})
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"container_image_ref": body.ContainerImageRef,
		"image_id":            response.ImageRef,
		"pulled":              true,
	})
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
	_, err := s.images.RemoveImage(r.Context(), &runtimeapi.RemoveImageRequest{
		Image: &runtimeapi.ImageSpec{Image: body.ContainerImageRef},
	})
	if err != nil {
		switch status.Code(err) {
		case codes.NotFound:
			jsonError(w, http.StatusNotFound, "image_not_found", err.Error())
		case codes.FailedPrecondition:
			jsonError(w, http.StatusConflict, "image_in_use", err.Error())
		default:
			jsonError(w, http.StatusInternalServerError, "internal_error", err.Error())
		}
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"container_image_ref": body.ContainerImageRef, "removed": true})
}

func (s *Server) workspaceSandboxes(ctx context.Context, workspaceUUID string) ([]*runtimeapi.PodSandbox, error) {
	labels := map[string]string{workspaceLabel: workspaceUUID}
	response, err := s.runtime.ListPodSandbox(ctx, &runtimeapi.ListPodSandboxRequest{
		Filter: &runtimeapi.PodSandboxFilter{LabelSelector: labels},
	})
	if err != nil {
		return nil, err
	}
	return response.Items, nil
}

func (s *Server) sandboxIP(ctx context.Context, sandboxID string) (netip.Addr, error) {
	response, err := s.runtime.PodSandboxStatus(ctx, &runtimeapi.PodSandboxStatusRequest{PodSandboxId: sandboxID})
	if err != nil {
		return netip.Addr{}, err
	}
	if response.Status == nil || response.Status.Network == nil {
		return netip.Addr{}, fmt.Errorf("sandbox %s has no network status", sandboxID)
	}
	ip, err := netip.ParseAddr(response.Status.Network.Ip)
	if err != nil || !ip.Is4() {
		return netip.Addr{}, fmt.Errorf("sandbox %s has invalid IPv4 address %q", sandboxID, response.Status.Network.Ip)
	}
	return ip, nil
}

func (s *Server) rebuildProxyState(ctx context.Context) error {
	response, err := s.runtime.ListPodSandbox(ctx, &runtimeapi.ListPodSandboxRequest{
		Filter: &runtimeapi.PodSandboxFilter{
			State: &runtimeapi.PodSandboxStateValue{State: runtimeapi.PodSandboxState_SANDBOX_READY},
		},
	})
	if err != nil {
		return err
	}
	for _, sandbox := range response.Items {
		workspaceUUID := sandbox.Labels[workspaceLabel]
		if workspaceUUID == "" {
			continue
		}
		ip, err := s.sandboxIP(ctx, sandbox.Id)
		if err != nil {
			return err
		}
		s.proxies.Store(workspaceUUID, ip)
	}
	return nil
}
