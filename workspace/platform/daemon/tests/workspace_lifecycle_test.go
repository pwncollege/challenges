package tests

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"slices"
	"strconv"
	"strings"
	"sync"
	"testing"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/test/bufconn"
	runtimeapi "k8s.io/cri-api/pkg/apis/runtime/v1"
	daemon "pwn.college/workspace/platform/daemon/internal"
)

type criState struct {
	mu             sync.Mutex
	sandbox        *runtimeapi.PodSandbox
	container      *runtimeapi.Container
	sandboxRequest *runtimeapi.RunPodSandboxRequest
	createRequest  *runtimeapi.CreateContainerRequest
}

type runtimeService struct {
	runtimeapi.UnimplementedRuntimeServiceServer
	state *criState
}

type imageService struct {
	runtimeapi.UnimplementedImageServiceServer
}

func (s *runtimeService) Version(context.Context, *runtimeapi.VersionRequest) (*runtimeapi.VersionResponse, error) {
	return &runtimeapi.VersionResponse{
		Version:           "0.1.0",
		RuntimeName:       "containerd",
		RuntimeVersion:    "2.3.0",
		RuntimeApiVersion: "v1",
	}, nil
}

func (s *runtimeService) Status(context.Context, *runtimeapi.StatusRequest) (*runtimeapi.StatusResponse, error) {
	return &runtimeapi.StatusResponse{
		Status: &runtimeapi.RuntimeStatus{Conditions: []*runtimeapi.RuntimeCondition{
			{Type: "RuntimeReady", Status: true},
			{Type: "NetworkReady", Status: true},
		}},
		RuntimeHandlers: []*runtimeapi.RuntimeHandler{{Name: "kata"}},
	}, nil
}

func (s *runtimeService) ListPodSandbox(_ context.Context, request *runtimeapi.ListPodSandboxRequest) (*runtimeapi.ListPodSandboxResponse, error) {
	s.state.mu.Lock()
	defer s.state.mu.Unlock()
	if s.state.sandbox == nil || !sandboxMatches(s.state.sandbox, request.Filter) {
		return &runtimeapi.ListPodSandboxResponse{}, nil
	}
	return &runtimeapi.ListPodSandboxResponse{Items: []*runtimeapi.PodSandbox{s.state.sandbox}}, nil
}

func sandboxMatches(sandbox *runtimeapi.PodSandbox, filter *runtimeapi.PodSandboxFilter) bool {
	if filter == nil {
		return true
	}
	if filter.Id != "" && filter.Id != sandbox.Id {
		return false
	}
	if filter.State != nil && filter.State.State != sandbox.State {
		return false
	}
	for name, value := range filter.LabelSelector {
		if sandbox.Labels[name] != value {
			return false
		}
	}
	return true
}

func (s *runtimeService) RunPodSandbox(_ context.Context, request *runtimeapi.RunPodSandboxRequest) (*runtimeapi.RunPodSandboxResponse, error) {
	s.state.mu.Lock()
	defer s.state.mu.Unlock()
	s.state.sandboxRequest = request
	s.state.sandbox = &runtimeapi.PodSandbox{
		Id:             "sandbox-id",
		Metadata:       request.Config.Metadata,
		State:          runtimeapi.PodSandboxState_SANDBOX_READY,
		Labels:         request.Config.Labels,
		RuntimeHandler: request.RuntimeHandler,
	}
	return &runtimeapi.RunPodSandboxResponse{PodSandboxId: "sandbox-id"}, nil
}

func (s *runtimeService) PodSandboxStatus(context.Context, *runtimeapi.PodSandboxStatusRequest) (*runtimeapi.PodSandboxStatusResponse, error) {
	s.state.mu.Lock()
	defer s.state.mu.Unlock()
	return &runtimeapi.PodSandboxStatusResponse{Status: &runtimeapi.PodSandboxStatus{
		Id:      s.state.sandbox.Id,
		State:   s.state.sandbox.State,
		Labels:  s.state.sandbox.Labels,
		Network: &runtimeapi.PodSandboxNetworkStatus{Ip: "127.0.0.2"},
	}}, nil
}

func (s *runtimeService) CreateContainer(_ context.Context, request *runtimeapi.CreateContainerRequest) (*runtimeapi.CreateContainerResponse, error) {
	s.state.mu.Lock()
	defer s.state.mu.Unlock()
	s.state.createRequest = request
	s.state.container = &runtimeapi.Container{
		Id:           "container-id",
		PodSandboxId: request.PodSandboxId,
		Metadata:     request.Config.Metadata,
		State:        runtimeapi.ContainerState_CONTAINER_CREATED,
		Labels:       request.Config.Labels,
	}
	return &runtimeapi.CreateContainerResponse{ContainerId: "container-id"}, nil
}

func (s *runtimeService) StartContainer(context.Context, *runtimeapi.StartContainerRequest) (*runtimeapi.StartContainerResponse, error) {
	s.state.mu.Lock()
	defer s.state.mu.Unlock()
	s.state.container.State = runtimeapi.ContainerState_CONTAINER_RUNNING
	return &runtimeapi.StartContainerResponse{}, nil
}

func (s *runtimeService) ListContainers(_ context.Context, request *runtimeapi.ListContainersRequest) (*runtimeapi.ListContainersResponse, error) {
	s.state.mu.Lock()
	defer s.state.mu.Unlock()
	if s.state.container == nil || request.Filter.PodSandboxId != s.state.container.PodSandboxId {
		return &runtimeapi.ListContainersResponse{}, nil
	}
	return &runtimeapi.ListContainersResponse{Containers: []*runtimeapi.Container{s.state.container}}, nil
}

func (s *runtimeService) StopContainer(context.Context, *runtimeapi.StopContainerRequest) (*runtimeapi.StopContainerResponse, error) {
	s.state.mu.Lock()
	defer s.state.mu.Unlock()
	s.state.container.State = runtimeapi.ContainerState_CONTAINER_EXITED
	return &runtimeapi.StopContainerResponse{}, nil
}

func (s *runtimeService) RemoveContainer(context.Context, *runtimeapi.RemoveContainerRequest) (*runtimeapi.RemoveContainerResponse, error) {
	s.state.mu.Lock()
	defer s.state.mu.Unlock()
	s.state.container = nil
	return &runtimeapi.RemoveContainerResponse{}, nil
}

func (s *runtimeService) StopPodSandbox(context.Context, *runtimeapi.StopPodSandboxRequest) (*runtimeapi.StopPodSandboxResponse, error) {
	s.state.mu.Lock()
	defer s.state.mu.Unlock()
	s.state.sandbox.State = runtimeapi.PodSandboxState_SANDBOX_NOTREADY
	return &runtimeapi.StopPodSandboxResponse{}, nil
}

func (s *runtimeService) RemovePodSandbox(context.Context, *runtimeapi.RemovePodSandboxRequest) (*runtimeapi.RemovePodSandboxResponse, error) {
	s.state.mu.Lock()
	defer s.state.mu.Unlock()
	s.state.sandbox = nil
	return &runtimeapi.RemovePodSandboxResponse{}, nil
}

func (*imageService) ImageStatus(context.Context, *runtimeapi.ImageStatusRequest) (*runtimeapi.ImageStatusResponse, error) {
	return &runtimeapi.ImageStatusResponse{Image: &runtimeapi.Image{Id: "sha256:test"}}, nil
}

func TestWorkspaceLifecycleAndProxy(t *testing.T) {
	agentListener, err := net.Listen("tcp4", "127.0.0.2:0")
	if err != nil {
		t.Fatal(err)
	}
	agentPort := uint16(agentListener.Addr().(*net.TCPAddr).Port)
	agentMux := http.NewServeMux()
	agentMux.HandleFunc("GET /health", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusOK)
	})
	agentMux.HandleFunc("POST /exec/", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]any{
			"method": r.Method,
			"path":   r.URL.Path,
			"query":  r.URL.RawQuery,
		})
	})
	agentServer := &http.Server{Handler: agentMux}
	go func() { _ = agentServer.Serve(agentListener) }()
	t.Cleanup(func() { _ = agentServer.Close() })

	state := &criState{}
	listener := bufconn.Listen(1 << 20)
	grpcServer := grpc.NewServer()
	runtimeapi.RegisterRuntimeServiceServer(grpcServer, &runtimeService{state: state})
	runtimeapi.RegisterImageServiceServer(grpcServer, &imageService{})
	go func() { _ = grpcServer.Serve(listener) }()
	t.Cleanup(grpcServer.Stop)
	containerd, err := grpc.NewClient(
		"passthrough:///containerd",
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithContextDialer(func(context.Context, string) (net.Conn, error) { return listener.Dial() }),
	)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = containerd.Close() })

	publicKey, privateKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	t.Setenv("PWN_WORKSPACE_PUBLIC_KEY", hex.EncodeToString(publicKey))
	nixStorePath := t.TempDir()
	workspacePath := "/nix/store/test-workspace"
	hostWorkspacePath := filepath.Join(nixStorePath, "test-workspace")
	if err := os.MkdirAll(filepath.Join(hostWorkspacePath, "bin"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(hostWorkspacePath, "bin", "workspace-entrypoint"), nil, 0o755); err != nil {
		t.Fatal(err)
	}
	t.Setenv("PWN_WORKSPACE_CONTAINERD_ADDRESS", "unix:///test/containerd.sock")
	t.Setenv("PWN_WORKSPACE_BRIDGE", "pwn-workspace0")
	t.Setenv("PWN_WORKSPACE_LOG_DIRECTORY", filepath.Join(t.TempDir(), "logs"))
	t.Setenv("PWN_WORKSPACE_NIX_STORE_PATH", nixStorePath)
	t.Setenv("PWN_WORKSPACE_PATH", workspacePath)
	t.Setenv("PWN_WORKSPACE_SECCOMP_PROFILE", filepath.Join(t.TempDir(), "seccomp.json"))
	t.Setenv("PWN_WORKSPACE_SUBNET", "127.0.0.0/29")
	t.Setenv("PWN_WORKSPACE_AGENT_PORT", strconv.Itoa(int(agentPort)))
	t.Setenv("PWN_WORKSPACE_VOLUME_BASE_PATH", "")
	cfg, err := daemon.LoadConfig()
	if err != nil {
		t.Fatal(err)
	}
	server := daemon.New(
		cfg,
		runtimeapi.NewRuntimeServiceClient(containerd),
		runtimeapi.NewImageServiceClient(containerd),
	)
	if err := server.Bootstrap(context.Background()); err != nil {
		t.Fatal(err)
	}
	workspaceDaemon := httptest.NewServer(server.Handler())
	t.Cleanup(workspaceDaemon.Close)

	workspaceUUID := "11111111-1111-4111-8111-111111111111"
	startBody := []byte(`{
		"runtime_config": {
			"container_image_ref": "test-workspace:latest",
			"entrypoint": ["/challenge/custom-init", "value"],
			"env": {"PWN_FLAG": "pwn.college{test}", "PWN_USER": "hacker", "TEST_VALUE": "present"}
		}
	}`)
	start := signedRequest(t, privateKey, http.MethodPost, "/api/workspaces/"+workspaceUUID+"/start", startBody, time.Now())
	start.URL.Scheme = "http"
	start.URL.Host = strings.TrimPrefix(workspaceDaemon.URL, "http://")
	startResponse, err := http.DefaultClient.Do(start)
	if err != nil {
		t.Fatal(err)
	}
	defer startResponse.Body.Close()
	if startResponse.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(startResponse.Body)
		t.Fatalf("start status = %d: %s", startResponse.StatusCode, body)
	}

	state.mu.Lock()
	sandboxRequest := state.sandboxRequest
	createRequest := state.createRequest
	state.mu.Unlock()
	if sandboxRequest.RuntimeHandler != "kata" {
		t.Errorf("runtime handler = %q, want kata", sandboxRequest.RuntimeHandler)
	}
	if sandboxRequest.Config.Labels["pwn.workspace-uuid"] != workspaceUUID {
		t.Errorf("sandbox labels = %#v", sandboxRequest.Config.Labels)
	}
	created := createRequest.Config
	if created.Image.Image != "test-workspace:latest" {
		t.Errorf("image = %q", created.Image.Image)
	}
	if !slices.Equal(created.Command, []string{"/bin/sh", "-c", `exec "$0" "$@"`, filepath.Join(workspacePath, "bin", "workspace-entrypoint")}) {
		t.Errorf("command = %v", created.Command)
	}
	if !slices.Equal(created.Args, []string{"/challenge/custom-init", "value"}) {
		t.Errorf("args = %v", created.Args)
	}
	environment := map[string]string{}
	for _, value := range created.Envs {
		environment[value.Key] = value.Value
	}
	if environment["PWN_FLAG"] != "pwn.college{test}" || environment["PWN_USER"] != "hacker" {
		t.Errorf("environment = %v", environment)
	}
	capabilities := created.Linux.SecurityContext.Capabilities.AddCapabilities
	for _, capability := range []string{"SYS_PTRACE", "SYS_ADMIN", "NET_ADMIN"} {
		if !slices.Contains(capabilities, capability) {
			t.Errorf("capabilities = %v, want %s", capabilities, capability)
		}
	}
	if len(created.Mounts) != 1 || created.Mounts[0].HostPath != nixStorePath || created.Mounts[0].ContainerPath != "/nix/store" || !created.Mounts[0].Readonly {
		t.Errorf("mounts = %#v", created.Mounts)
	}

	proxiedResponse, err := http.Post(workspaceDaemon.URL+"/w/"+workspaceUUID+"/exec/?value=1", "application/json", strings.NewReader(`{"argv":["true"]}`))
	if err != nil {
		t.Fatal(err)
	}
	defer proxiedResponse.Body.Close()
	if proxiedResponse.StatusCode != http.StatusOK {
		t.Fatalf("proxy status = %d", proxiedResponse.StatusCode)
	}
	var proxied map[string]any
	if err := json.NewDecoder(proxiedResponse.Body).Decode(&proxied); err != nil {
		t.Fatal(err)
	}
	if proxied["path"] != "/exec/" || proxied["query"] != "value=1" {
		t.Errorf("proxied request = %#v", proxied)
	}

	stop := signedRequest(t, privateKey, http.MethodPost, "/api/workspaces/"+workspaceUUID+"/stop", nil, time.Now())
	stop.URL.Scheme = "http"
	stop.URL.Host = strings.TrimPrefix(workspaceDaemon.URL, "http://")
	stopResponse, err := http.DefaultClient.Do(stop)
	if err != nil {
		t.Fatal(err)
	}
	defer stopResponse.Body.Close()
	if stopResponse.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(stopResponse.Body)
		t.Fatalf("stop status = %d: %s", stopResponse.StatusCode, body)
	}

	state.mu.Lock()
	sandboxRemoved := state.sandbox == nil
	containerRemoved := state.container == nil
	state.mu.Unlock()
	if !sandboxRemoved || !containerRemoved {
		t.Errorf("CRI resources remain after stop: sandbox=%v container=%v", !sandboxRemoved, !containerRemoved)
	}
	missing, err := http.Get(workspaceDaemon.URL + "/w/" + workspaceUUID + "/")
	if err != nil {
		t.Fatal(err)
	}
	defer missing.Body.Close()
	if missing.StatusCode != http.StatusNotFound {
		t.Fatalf("proxy after stop status = %d, want 404", missing.StatusCode)
	}
}

func signedRequest(
	t *testing.T,
	privateKey ed25519.PrivateKey,
	method string,
	requestURI string,
	body []byte,
	timestamp time.Time,
) *http.Request {
	t.Helper()
	request, err := http.NewRequest(method, requestURI, bytes.NewReader(body))
	if err != nil {
		t.Fatal(err)
	}
	timestampValue := strconv.FormatInt(timestamp.Unix(), 10)
	sum := sha256.Sum256(body)
	canonical := method + "\n" + request.URL.RequestURI() + "\n" + timestampValue + "\n" + hex.EncodeToString(sum[:])
	request.Header.Set("X-Pwn-Workspace-Timestamp", timestampValue)
	request.Header.Set("X-Pwn-Workspace-Signature", base64.StdEncoding.EncodeToString(ed25519.Sign(privateKey, []byte(canonical))))
	request.Header.Set("Content-Type", "application/json")
	return request
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}
