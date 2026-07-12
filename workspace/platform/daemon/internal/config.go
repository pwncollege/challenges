package daemon

import (
	"crypto/ed25519"
	"encoding/hex"
	"errors"
	"fmt"
	"net"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

type Config struct {
	listenAddress     string
	containerdAddress string
	egressAddress     string
	logDirectory      string
	nixStorePath      string
	publicKey         ed25519.PublicKey
	seccompProfile    string
	volumeBasePath    string
	workspacePath     string
	agentPort         uint16
}

func LoadConfig() (Config, error) {
	env := envReader{}
	containerdAddress := env.required("PWN_WORKSPACE_CONTAINERD_ADDRESS")
	egressAddress := env.required("PWN_WORKSPACE_EGRESS_ADDRESS")
	logDirectory := env.required("PWN_WORKSPACE_LOG_DIRECTORY")
	nixStorePath := env.required("PWN_WORKSPACE_NIX_STORE_PATH")
	seccompProfile := env.required("PWN_WORKSPACE_SECCOMP_PROFILE")
	workspacePath := env.required("PWN_WORKSPACE_PATH")
	if err := env.err(); err != nil {
		return Config{}, err
	}

	var publicKey ed25519.PublicKey
	if value := os.Getenv("PWN_WORKSPACE_PUBLIC_KEY"); value != "" {
		var err error
		publicKey, err = parsePublicKey(value)
		if err != nil {
			return Config{}, err
		}
	}
	if !filepath.IsAbs(workspacePath) {
		return Config{}, errors.New("PWN_WORKSPACE_PATH must be absolute")
	}
	if net.ParseIP(egressAddress).To4() == nil {
		return Config{}, errors.New("PWN_WORKSPACE_EGRESS_ADDRESS must be an IPv4 address")
	}
	if !filepath.IsAbs(nixStorePath) {
		return Config{}, errors.New("PWN_WORKSPACE_NIX_STORE_PATH must be absolute")
	}
	if !filepath.IsAbs(logDirectory) {
		return Config{}, errors.New("PWN_WORKSPACE_LOG_DIRECTORY must be absolute")
	}
	if !filepath.IsAbs(seccompProfile) {
		return Config{}, errors.New("PWN_WORKSPACE_SECCOMP_PROFILE must be absolute")
	}
	cleanWorkspacePath := filepath.Clean(workspacePath)
	relativeWorkspacePath, err := filepath.Rel("/nix/store", cleanWorkspacePath)
	if err != nil || relativeWorkspacePath == "." || relativeWorkspacePath == ".." || strings.HasPrefix(relativeWorkspacePath, ".."+string(filepath.Separator)) {
		return Config{}, errors.New("PWN_WORKSPACE_PATH must be within /nix/store")
	}
	volumeBasePath := os.Getenv("PWN_WORKSPACE_VOLUME_BASE_PATH")
	if volumeBasePath != "" && !filepath.IsAbs(volumeBasePath) {
		return Config{}, errors.New("PWN_WORKSPACE_VOLUME_BASE_PATH must be absolute")
	}
	agentPort, err := parsePort(getenv("PWN_WORKSPACE_AGENT_PORT", "8000"))
	if err != nil {
		return Config{}, fmt.Errorf("PWN_WORKSPACE_AGENT_PORT: %w", err)
	}
	cleanVolumeBasePath := ""
	if volumeBasePath != "" {
		cleanVolumeBasePath = filepath.Clean(volumeBasePath)
	}
	return Config{
		listenAddress:     getenv("PWN_WORKSPACE_DAEMON_LISTEN_ADDRESS", "127.0.0.1:8000"),
		containerdAddress: containerdAddress,
		egressAddress:     egressAddress,
		logDirectory:      filepath.Clean(logDirectory),
		nixStorePath:      filepath.Clean(nixStorePath),
		publicKey:         publicKey,
		seccompProfile:    filepath.Clean(seccompProfile),
		volumeBasePath:    cleanVolumeBasePath,
		workspacePath:     cleanWorkspacePath,
		agentPort:         agentPort,
	}, nil
}

func (c Config) ContainerdAddress() string {
	return c.containerdAddress
}

func (c Config) hostWorkspacePath() string {
	relative, _ := filepath.Rel("/nix/store", c.workspacePath)
	return filepath.Join(c.nixStorePath, relative)
}

func parsePublicKey(value string) (ed25519.PublicKey, error) {
	publicKey, err := hex.DecodeString(value)
	if err != nil {
		return nil, fmt.Errorf("decode control plane public key: %w", err)
	}
	if len(publicKey) != ed25519.PublicKeySize {
		return nil, fmt.Errorf("control plane public key must be %d bytes", ed25519.PublicKeySize)
	}
	return ed25519.PublicKey(publicKey), nil
}

func parsePort(value string) (uint16, error) {
	port, err := strconv.ParseUint(value, 10, 16)
	if err != nil || port == 0 {
		return 0, errors.New("must be a port between 1 and 65535")
	}
	return uint16(port), nil
}

func getenv(name, fallback string) string {
	if value := os.Getenv(name); value != "" {
		return value
	}
	return fallback
}

type envReader struct {
	missing []string
}

func (e *envReader) required(name string) string {
	if value := os.Getenv(name); value != "" {
		return value
	}
	e.missing = append(e.missing, name)
	return ""
}

func (e *envReader) err() error {
	if len(e.missing) == 0 {
		return nil
	}
	return fmt.Errorf("missing required environment variables: %s", strings.Join(e.missing, ", "))
}
