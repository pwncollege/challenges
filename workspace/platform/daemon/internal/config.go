package daemon

import (
	"crypto/ed25519"
	"encoding/hex"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

type Config struct {
	listenAddress  string
	nixStorePath   string
	publicKey      ed25519.PublicKey
	volumeBasePath string
	dockerNetwork  string
	workspacePath  string
	agentPort      uint16
}

func LoadConfig() (Config, error) {
	env := envReader{}
	nixStorePath := env.required("PWN_WORKSPACE_NIX_STORE_PATH")
	workspacePath := env.required("PWN_WORKSPACE_PATH")
	dockerNetwork := env.required("PWN_WORKSPACE_DOCKER_NETWORK")
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
	if !filepath.IsAbs(nixStorePath) {
		return Config{}, errors.New("PWN_WORKSPACE_NIX_STORE_PATH must be absolute")
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
		listenAddress:  getenv("PWN_WORKSPACE_DAEMON_LISTEN_ADDRESS", "127.0.0.1:8000"),
		nixStorePath:   filepath.Clean(nixStorePath),
		publicKey:      publicKey,
		volumeBasePath: cleanVolumeBasePath,
		dockerNetwork:  dockerNetwork,
		workspacePath:  cleanWorkspacePath,
		agentPort:      agentPort,
	}, nil
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
