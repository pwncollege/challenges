package workspace

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/pelletier/go-toml/v2"
)

const workspaceServicesDir = "/run/workspace/user/services"

type serviceDefinition struct {
	Name         string   `toml:"name"`
	SocketPath   string   `toml:"socket_path"`
	URL          string   `toml:"url"`
	StartTimeout string   `toml:"start_timeout"`
	ReadyPath    string   `toml:"ready_path"`
	Command      []string `toml:"command"`
}

type managedService struct {
	name    string
	command *exec.Cmd
	proxy   *httputil.ReverseProxy
	exited  bool
}

type serviceManager struct {
	logger      *slog.Logger
	mu          sync.Mutex
	definitions map[string]serviceDefinition
	services    map[string]*managedService
}

func newServiceManager(logger *slog.Logger) *serviceManager {
	return &serviceManager{
		logger:      logger,
		definitions: make(map[string]serviceDefinition),
		services:    make(map[string]*managedService),
	}
}

func (a *agent) serviceHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		serviceName, ok := requestedServiceName(r.URL.Path)
		if !ok {
			http.Error(w, "missing service name", http.StatusBadRequest)
			return
		}
		proxy, err := a.services.proxy(r.Context(), serviceName)
		if errors.Is(err, errUnknownService) {
			http.Error(w, err.Error(), http.StatusNotFound)
			return
		}
		if err != nil {
			a.logger.Warn("service unavailable", "service", serviceName, "err", err)
			http.Error(w, err.Error(), http.StatusBadGateway)
			return
		}
		proxy.ServeHTTP(w, r)
	}
}

var errUnknownService = errors.New("unknown service")

func requestedServiceName(requestPath string) (string, bool) {
	remainder := strings.TrimPrefix(requestPath, "/service/")
	serviceName, _, _ := strings.Cut(remainder, "/")
	return serviceName, serviceName != ""
}

func (m *serviceManager) proxy(ctx context.Context, name string) (*httputil.ReverseProxy, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	definition, err := m.definitionLocked(name)
	if err != nil {
		return nil, err
	}

	service := m.services[name]
	if service == nil {
		proxy, err := serviceProxy(definition, m.logger)
		if err != nil {
			return nil, err
		}
		service = &managedService{
			name:  name,
			proxy: proxy,
		}
		m.services[name] = service
	}

	if service.command != nil && !service.exited {
		return service.proxy, nil
	}

	if err := m.startLocked(ctx, service, definition); err != nil {
		return nil, err
	}
	return service.proxy, nil
}

func (m *serviceManager) definitionLocked(name string) (serviceDefinition, error) {
	if definition, ok := m.definitions[name]; ok {
		return definition, nil
	}
	definitionPath := filepath.Join(workspaceServicesDir, name+".toml")
	definition, err := loadServiceDefinition(definitionPath)
	if errors.Is(err, os.ErrNotExist) {
		return serviceDefinition{}, fmt.Errorf("%w: %s", errUnknownService, name)
	}
	if err != nil {
		return serviceDefinition{}, err
	}
	if definition.Name != name {
		return serviceDefinition{}, fmt.Errorf("service definition name mismatch: requested %s, got %s", name, definition.Name)
	}
	m.definitions[name] = definition
	return definition, nil
}

func (m *serviceManager) startLocked(ctx context.Context, service *managedService, definition serviceDefinition) error {
	if definition.SocketPath != "" {
		if err := os.MkdirAll(filepath.Dir(definition.SocketPath), 0700); err != nil {
			return err
		}
		if err := os.Remove(definition.SocketPath); err != nil && !errors.Is(err, os.ErrNotExist) {
			return err
		}
	}

	command := exec.Command(definition.Command[0], definition.Command[1:]...)
	command.Stdout = os.Stderr
	command.Stderr = os.Stderr
	command.Env = os.Environ()
	command.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}

	if err := command.Start(); err != nil {
		return err
	}
	service.command = command
	service.exited = false
	m.logger.Info("started workspace service", "service", service.name, "pid", command.Process.Pid)

	go m.waitForService(service, command)

	readyCtx, cancel := context.WithTimeout(ctx, definition.startTimeout())
	defer cancel()
	if err := waitForServiceHTTP(readyCtx, definition); err != nil {
		killProcessGroup(command)
		service.exited = true
		return fmt.Errorf("service %s did not become ready: %w", service.name, err)
	}
	return nil
}

func (m *serviceManager) waitForService(service *managedService, command *exec.Cmd) {
	err := command.Wait()
	m.mu.Lock()
	if service.command == command {
		service.exited = true
	}
	m.mu.Unlock()
	if err != nil {
		m.logger.Warn("workspace service exited", "service", service.name, "err", err)
	} else {
		m.logger.Info("workspace service exited", "service", service.name)
	}
}

func (m *serviceManager) stopAll() {
	m.mu.Lock()
	commands := make([]*exec.Cmd, 0, len(m.services))
	for _, service := range m.services {
		if service.command != nil && !service.exited {
			commands = append(commands, service.command)
		}
	}
	m.mu.Unlock()
	for _, command := range commands {
		killProcessGroup(command)
	}
}

func serviceProxy(definition serviceDefinition, logger *slog.Logger) (*httputil.ReverseProxy, error) {
	target, err := definition.targetURL()
	if err != nil {
		return nil, err
	}
	proxy := httputil.NewSingleHostReverseProxy(target)
	proxy.Director = func(request *http.Request) {
		request.URL.Scheme = target.Scheme
		request.URL.Host = target.Host
		request.URL.Path = stripServicePrefix(definition.Name, request.URL.Path)
		request.URL.RawPath = ""
	}
	if definition.SocketPath != "" {
		proxy.Transport = unixSocketTransport(definition.SocketPath)
	}
	proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
		logger.Warn("service proxy failed", "service", definition.Name, "path", r.URL.Path, "err", err)
		http.Error(w, err.Error(), http.StatusBadGateway)
	}
	return proxy, nil
}

func stripServicePrefix(serviceName string, requestPath string) string {
	prefix := "/service/" + serviceName
	stripped := strings.TrimPrefix(requestPath, prefix)
	if stripped == "" {
		return "/"
	}
	if !strings.HasPrefix(stripped, "/") {
		return "/" + stripped
	}
	return stripped
}

func unixSocketTransport(socketPath string) *http.Transport {
	return &http.Transport{
		DialContext: func(ctx context.Context, _, _ string) (net.Conn, error) {
			var dialer net.Dialer
			return dialer.DialContext(ctx, "unix", socketPath)
		},
	}
}

func waitForServiceHTTP(ctx context.Context, definition serviceDefinition) error {
	target, err := definition.targetURL()
	if err != nil {
		return err
	}
	readyURL := target.ResolveReference(&url.URL{Path: definition.readyPath()})
	client := &http.Client{Timeout: 500 * time.Millisecond}
	if definition.SocketPath != "" {
		client.Transport = unixSocketTransport(definition.SocketPath)
	}

	for {
		request, err := http.NewRequestWithContext(ctx, http.MethodGet, readyURL.String(), nil)
		if err != nil {
			return err
		}
		response, err := client.Do(request)
		if err == nil {
			response.Body.Close()
			if response.StatusCode < http.StatusInternalServerError {
				return nil
			}
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(100 * time.Millisecond):
		}
	}
}

func loadServiceDefinition(path string) (serviceDefinition, error) {
	var definition serviceDefinition
	contents, err := os.ReadFile(path)
	if err != nil {
		return definition, err
	}
	if err := toml.Unmarshal(contents, &definition); err != nil {
		return definition, fmt.Errorf("%s: %w", path, err)
	}
	if err := definition.validate(); err != nil {
		return definition, fmt.Errorf("%s: %w", path, err)
	}
	return definition, nil
}

func (d serviceDefinition) validate() error {
	if d.Name == "" {
		return errors.New("service name is required")
	}
	if strings.Contains(d.Name, "/") {
		return fmt.Errorf("service name contains slash: %s", d.Name)
	}
	if (d.SocketPath == "") == (d.URL == "") {
		return errors.New("exactly one of socket_path or url is required")
	}
	if len(d.Command) == 0 {
		return errors.New("command is required")
	}
	if d.StartTimeout != "" {
		if _, err := time.ParseDuration(d.StartTimeout); err != nil {
			return fmt.Errorf("invalid start_timeout: %w", err)
		}
	}
	return nil
}

func (d serviceDefinition) targetURL() (*url.URL, error) {
	if d.URL != "" {
		return url.Parse(d.URL)
	}
	return &url.URL{Scheme: "http", Host: d.Name + ".workspace"}, nil
}

func (d serviceDefinition) readyPath() string {
	if d.ReadyPath == "" {
		return "/"
	}
	return d.ReadyPath
}

func (d serviceDefinition) startTimeout() time.Duration {
	if d.StartTimeout == "" {
		return 5 * time.Second
	}
	timeout, err := time.ParseDuration(d.StartTimeout)
	if err != nil {
		return 5 * time.Second
	}
	return timeout
}
