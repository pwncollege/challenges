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
	volumeLocks   map[string]struct{}
	volumeLocksMu sync.Mutex
}

func New(cfg Config, runtime runtimeapi.RuntimeServiceClient, images runtimeapi.ImageServiceClient) *Server {
	return &Server{
		config:      cfg,
		runtime:     runtime,
		images:      images,
		volumeLocks: map[string]struct{}{},
	}
}

func (s *Server) Bootstrap(ctx context.Context) error {
	if s.config.volumeBasePath != "" {
		if err := assertBtrfsPath(s.config.volumeBasePath); err != nil {
			return err
		}
	}
	if err := assertWorkspacePath(s.config.hostWorkspacePath()); err != nil {
		return err
	}
	if err := os.MkdirAll(s.config.logDirectory, 0o711); err != nil {
		return err
	}
	if err := s.validateWorkspaceRoutes(); err != nil {
		return err
	}
	if _, err := s.runtime.Version(ctx, &runtimeapi.VersionRequest{Version: "0.1.0"}); err != nil {
		return err
	}
	return s.rebuildProxyState(ctx)
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
