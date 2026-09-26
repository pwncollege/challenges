package daemon

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"sync"

	runtimeapi "k8s.io/cri-api/pkg/apis/runtime/v1"
)

type Server struct {
	config        Config
	runtime       runtimeapi.RuntimeServiceClient
	images        runtimeapi.ImageServiceClient
	proxies       sync.Map
	resourceLocks sync.Map
}

func New(cfg Config, runtime runtimeapi.RuntimeServiceClient, images runtimeapi.ImageServiceClient) *Server {
	return &Server{
		config:  cfg,
		runtime: runtime,
		images:  images,
	}
}

func (s *Server) Bootstrap(ctx context.Context) error {
	if s.config.volumeBasePath != "" {
		if err := os.MkdirAll(s.config.volumeBasePath, 0700); err != nil {
			return err
		}
	}
	if err := assertWorkspacePath(s.config.hostWorkspacePath()); err != nil {
		return err
	}
	if err := os.MkdirAll(s.config.logDirectory, 0o711); err != nil {
		return err
	}
	if err := s.checkRuntimeReady(ctx, true); err != nil {
		return err
	}
	return s.rebuildProxyState(ctx)
}

func (s *Server) checkRuntimeReady(ctx context.Context, requireKata bool) error {
	response, err := s.runtime.Status(ctx, &runtimeapi.StatusRequest{})
	if err != nil {
		return err
	}
	runtimeReady := false
	networkReady := false
	for _, condition := range response.Status.GetConditions() {
		switch condition.Type {
		case "RuntimeReady":
			runtimeReady = condition.Status
		case "NetworkReady":
			networkReady = condition.Status
		}
	}
	if !runtimeReady || !networkReady {
		return fmt.Errorf("container runtime is not ready")
	}
	if !requireKata {
		return nil
	}
	for _, handler := range response.RuntimeHandlers {
		if handler.Name == kataRuntime {
			return nil
		}
	}
	return fmt.Errorf("Kata runtime is unavailable")
}

func assertWorkspacePath(path string) error {
	entrypoint := filepath.Join(path, "bin", "workspace-entrypoint")
	info, err := os.Stat(entrypoint)
	if err != nil {
		return fmt.Errorf("workspace entrypoint: %w", err)
	}
	if !info.Mode().IsRegular() || info.Mode().Perm()&0o111 == 0 {
		return fmt.Errorf("workspace entrypoint %s is not executable", entrypoint)
	}
	return nil
}
