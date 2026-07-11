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
	"fmt"
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

	dockercontainer "github.com/docker/docker/api/types/container"
	dockernetwork "github.com/docker/docker/api/types/network"
	dockerclient "github.com/docker/docker/client"
	daemon "pwn.college/workspace/platform/daemon/internal"
)

type capturedContainerCreate struct {
	config     dockercontainer.Config
	host       dockercontainer.HostConfig
	networking dockernetwork.NetworkingConfig
	name       string
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
	t.Cleanup(func() {
		_ = agentServer.Close()
	})

	var captured capturedContainerCreate
	var captureMu sync.Mutex
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		path := stripDockerAPIVersion(r.URL.Path)
		switch {
		case (r.Method == http.MethodGet || r.Method == http.MethodHead) && path == "/_ping":
			w.Header().Set("API-Version", "1.47")
			_, _ = w.Write([]byte("OK"))
		case r.Method == http.MethodGet && path == "/networks/workspace-test":
			writeJSON(w, http.StatusOK, map[string]any{
				"Name":   "workspace-test",
				"Driver": "bridge",
				"Labels": map[string]string{"pwn.workspace-network": "true"},
				"IPAM": map[string]any{
					"Config": []map[string]string{{"Subnet": "127.0.0.0/29", "Gateway": "127.0.0.1"}},
				},
				"Containers": map[string]any{},
			})
		case r.Method == http.MethodGet && path == "/containers/json":
			writeJSON(w, http.StatusOK, []any{})
		case r.Method == http.MethodGet && path == "/images/test-workspace:latest/json":
			writeJSON(w, http.StatusOK, map[string]any{"Id": "sha256:test"})
		case r.Method == http.MethodPost && path == "/containers/create":
			data, err := io.ReadAll(r.Body)
			if err != nil {
				t.Error(err)
			}
			var config dockercontainer.Config
			var envelope struct {
				HostConfig       dockercontainer.HostConfig     `json:"HostConfig"`
				NetworkingConfig dockernetwork.NetworkingConfig `json:"NetworkingConfig"`
			}
			if err := json.Unmarshal(data, &config); err != nil {
				t.Error(err)
			}
			if err := json.Unmarshal(data, &envelope); err != nil {
				t.Error(err)
			}
			captureMu.Lock()
			captured = capturedContainerCreate{
				config:     config,
				host:       envelope.HostConfig,
				networking: envelope.NetworkingConfig,
				name:       r.URL.Query().Get("name"),
			}
			captureMu.Unlock()
			writeJSON(w, http.StatusCreated, map[string]any{"Id": "container-id", "Warnings": []string{}})
		case r.Method == http.MethodPost && path == "/containers/container-id/start":
			w.WriteHeader(http.StatusNoContent)
		case r.Method == http.MethodPost && strings.HasPrefix(path, "/containers/") && strings.HasSuffix(path, "/stop"):
			w.WriteHeader(http.StatusNoContent)
		default:
			http.Error(w, fmt.Sprintf("unexpected Docker request: %s %s", r.Method, r.URL.RequestURI()), http.StatusNotFound)
		}
	}))
	t.Cleanup(engine.Close)
	docker, err := dockerclient.NewClientWithOpts(
		dockerclient.WithHost(engine.URL),
		dockerclient.WithHTTPClient(engine.Client()),
		dockerclient.WithVersion("1.47"),
	)
	if err != nil {
		t.Fatal(err)
	}

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
	t.Setenv("PWN_WORKSPACE_NIX_STORE_PATH", nixStorePath)
	t.Setenv("PWN_WORKSPACE_PATH", workspacePath)
	t.Setenv("PWN_WORKSPACE_DOCKER_NETWORK", "workspace-test")
	t.Setenv("PWN_WORKSPACE_AGENT_PORT", strconv.Itoa(int(agentPort)))
	t.Setenv("PWN_WORKSPACE_VOLUME_BASE_PATH", "")
	cfg, err := daemon.LoadConfig()
	if err != nil {
		t.Fatal(err)
	}
	server := daemon.New(cfg, docker)
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

	captureMu.Lock()
	created := captured
	captureMu.Unlock()
	if created.name != workspaceUUID {
		t.Errorf("container name = %q, want %q", created.name, workspaceUUID)
	}
	if created.config.Image != "test-workspace:latest" {
		t.Errorf("image = %q", created.config.Image)
	}
	if got := []string(created.config.Entrypoint); !slices.Equal(got, []string{"/bin/sh", "-c", `exec "$0" "$@"`, filepath.Join(workspacePath, "bin", "workspace-entrypoint")}) {
		t.Errorf("entrypoint = %v", got)
	}
	if got := []string(created.config.Cmd); !slices.Equal(got, []string{"/challenge/custom-init", "value"}) {
		t.Errorf("command = %v", got)
	}
	if !slices.Contains(created.config.Env, "PWN_FLAG=pwn.college{test}") || !slices.Contains(created.config.Env, "PWN_USER=hacker") {
		t.Errorf("environment = %v", created.config.Env)
	}
	if created.host.Runtime != "kata" {
		t.Errorf("runtime = %q, want kata", created.host.Runtime)
	}
	for _, capability := range []string{"CAP_SYS_PTRACE", "CAP_SYS_ADMIN", "CAP_NET_ADMIN"} {
		if !slices.Contains([]string(created.host.CapAdd), capability) {
			t.Errorf("capabilities = %v, want %s", created.host.CapAdd, capability)
		}
	}
	if len(created.host.Mounts) != 1 || created.host.Mounts[0].Source != nixStorePath || created.host.Mounts[0].Target != "/nix/store" || !created.host.Mounts[0].ReadOnly {
		t.Errorf("mounts = %#v", created.host.Mounts)
	}
	endpoint := created.networking.EndpointsConfig["workspace-test"]
	if endpoint == nil || endpoint.IPAMConfig == nil || endpoint.IPAMConfig.IPv4Address != "127.0.0.2" {
		t.Errorf("network endpoint = %#v", endpoint)
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

func stripDockerAPIVersion(path string) string {
	parts := strings.SplitN(strings.TrimPrefix(path, "/"), "/", 2)
	if len(parts) == 2 && strings.HasPrefix(parts[0], "v1.") {
		return "/" + parts[1]
	}
	return path
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}
