package daemon

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"sync"

	dockerclient "github.com/docker/docker/client"
)

type Server struct {
	config        Config
	docker        *dockerclient.Client
	ipam          *ipAllocator
	proxies       sync.Map
	volumeLocks   map[string]struct{}
	volumeLocksMu sync.Mutex
}

func New(cfg Config, docker *dockerclient.Client) *Server {
	return &Server{
		config:      cfg,
		docker:      docker,
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

	if _, err := s.docker.Ping(ctx); err != nil {
		return err
	}
	subnet, reservedAddresses, err := s.workspaceNetworkConfig(ctx)
	if err != nil {
		return err
	}
	ipam, err := newIPAllocator(subnet)
	if err != nil {
		return err
	}
	for _, address := range reservedAddresses {
		if address == subnet.Addr().Next() {
			continue
		}
		if err := ipam.reserve(address); err != nil {
			return fmt.Errorf("reserve network address %s: %w", address, err)
		}
	}
	s.ipam = ipam
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
