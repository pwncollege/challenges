package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
)

const agentUID = 1000
const agentGID = 1000
const workspaceRunDir = "/run/workspace"
const workspaceUserRunDir = "/run/workspace/user"
const workspaceServicesDir = "/run/workspace/user/services"

type controlMessage struct {
	Type    string `json:"type"`
	Message string `json:"message,omitempty"`
}

type workspaceConfig struct {
	flag string
	user string
	home string
}

func main() {
	logger := slog.New(slog.NewTextHandler(os.Stderr, nil))

	config, err := loadWorkspaceConfig()
	if err != nil {
		logger.Error("invalid workspace configuration", "err", err)
		os.Exit(1)
	}
	if err := prepareWorkspace(config); err != nil {
		logger.Error("failed to prepare workspace", "err", err)
		os.Exit(1)
	}

	controlRead, controlWrite, err := os.Pipe()
	if err != nil {
		logger.Error("failed to create control pipe", "err", err)
		os.Exit(1)
	}

	agent, err := startAgent(controlRead, config)
	controlRead.Close()
	if err != nil {
		logger.Error("failed to start workspace agent", "err", err)
		os.Exit(1)
	}

	setupErr := runChallengeInit()
	if setupErr != nil {
		logger.Error("workspace setup failed", "err", setupErr)
		sendControl(controlWrite, controlMessage{Type: "failed", Message: setupErr.Error()})
	} else {
		sendControl(controlWrite, controlMessage{Type: "ready"})
	}
	controlWrite.Close()

	execSupervisor(agent.Process.Pid)
}

func startAgent(controlRead *os.File, config workspaceConfig) (*exec.Cmd, error) {
	executable, err := os.Executable()
	if err != nil {
		return nil, err
	}
	agentPath := filepath.Join(filepath.Dir(executable), "workspace-agent")
	command := exec.Command(agentPath)
	command.Stdout = os.Stdout
	command.Stderr = os.Stderr
	command.ExtraFiles = []*os.File{controlRead}
	command.Env = append(os.Environ(),
		"HOME="+config.home,
		"LOGNAME="+config.user,
		"SHELL=/bin/bash",
		"USER="+config.user,
	)
	command.SysProcAttr = &syscall.SysProcAttr{
		Setpgid: true,
		Credential: &syscall.Credential{
			Uid: agentUID,
			Gid: agentGID,
		},
	}
	return command, command.Start()
}

func execSupervisor(agentPID int) {
	executable, err := os.Executable()
	if err != nil {
		panic(err)
	}
	supervisorPath := filepath.Join(filepath.Dir(executable), "workspace-supervisor")
	environment := append(os.Environ(), "WORKSPACE_AGENT_PID="+fmt.Sprint(agentPID))
	if err := syscall.Exec(supervisorPath, []string{supervisorPath}, environment); err != nil {
		panic(err)
	}
}

func loadWorkspaceConfig() (workspaceConfig, error) {
	flag := os.Getenv("PWN_FLAG")
	os.Unsetenv("PWN_FLAG")
	if flag == "" {
		return workspaceConfig{}, errors.New("PWN_FLAG is not set")
	}

	user := os.Getenv("PWN_USER")
	if user == "" {
		user = "hacker"
	}
	if strings.ContainsAny(user, ":/\n\r") || user == "." || user == ".." {
		return workspaceConfig{}, fmt.Errorf("invalid PWN_USER %q", user)
	}
	return workspaceConfig{
		flag: flag,
		user: user,
		home: filepath.Join("/home", user),
	}, nil
}

func prepareWorkspace(config workspaceConfig) error {
	if err := setupUser(config.user, config.home); err != nil {
		return err
	}
	if err := setupRunDirectories(); err != nil {
		return err
	}
	if err := writeFlag(config.flag); err != nil {
		return fmt.Errorf("write flag: %w", err)
	}
	return nil
}

func setupRunDirectories() error {
	if err := os.MkdirAll(workspaceRunDir, 0755); err != nil {
		return err
	}
	if err := os.Chmod(workspaceRunDir, 0755); err != nil {
		return err
	}
	for _, directory := range []string{workspaceUserRunDir, workspaceServicesDir} {
		if err := os.MkdirAll(directory, 0700); err != nil {
			return err
		}
		if err := os.Chown(directory, agentUID, agentGID); err != nil {
			return err
		}
		if err := os.Chmod(directory, 0700); err != nil {
			return err
		}
	}
	return linkServiceDefinitions()
}

func runChallengeInit() error {
	if err := runInit(); err != nil {
		return fmt.Errorf("run .init: %w", err)
	}
	return nil
}

func setupUser(user string, home string) error {
	if err := upsertPasswdUser(user, home); err != nil {
		return err
	}
	if err := upsertGroup(user); err != nil {
		return err
	}
	if _, err := os.Stat(home); errors.Is(err, os.ErrNotExist) {
		if err := os.MkdirAll(home, 0755); err != nil {
			return err
		}
		if err := os.Chown(home, agentUID, agentGID); err != nil {
			return err
		}
	} else if err != nil {
		return err
	}
	return nil
}

func upsertPasswdUser(user string, home string) error {
	const passwdPath = "/etc/passwd"

	data, err := os.ReadFile(passwdPath)
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}

	lines := make([]string, 0)
	found := false
	for _, line := range strings.Split(strings.TrimRight(string(data), "\n"), "\n") {
		if line == "" {
			continue
		}
		fields := strings.Split(line, ":")
		if len(fields) < 7 {
			lines = append(lines, line)
			continue
		}
		uid, _ := strconv.Atoi(fields[2])
		if fields[0] == user || uid == agentUID {
			if found {
				continue
			}
			fields[0] = user
			fields[2] = strconv.Itoa(agentUID)
			fields[3] = strconv.Itoa(agentGID)
			fields[5] = home
			fields[6] = "/bin/bash"
			lines = append(lines, strings.Join(fields, ":"))
			found = true
			continue
		}
		lines = append(lines, line)
	}
	if !found {
		lines = append(lines, fmt.Sprintf("%s:x:%d:%d::%s:/bin/bash", user, agentUID, agentGID, home))
	}
	return writeLines(passwdPath, lines, 0644)
}

func upsertGroup(user string) error {
	const groupPath = "/etc/group"

	data, err := os.ReadFile(groupPath)
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}

	lines := make([]string, 0)
	found := false
	for _, line := range strings.Split(strings.TrimRight(string(data), "\n"), "\n") {
		if line == "" {
			continue
		}
		fields := strings.Split(line, ":")
		if len(fields) < 4 {
			lines = append(lines, line)
			continue
		}
		gid, _ := strconv.Atoi(fields[2])
		if fields[0] == user || gid == agentGID {
			if found {
				continue
			}
			fields[0] = user
			fields[2] = strconv.Itoa(agentGID)
			lines = append(lines, strings.Join(fields, ":"))
			found = true
			continue
		}
		lines = append(lines, line)
	}
	if !found {
		lines = append(lines, fmt.Sprintf("%s:x:%d:", user, agentGID))
	}
	return writeLines(groupPath, lines, 0644)
}

func writeLines(path string, lines []string, mode os.FileMode) error {
	var buffer bytes.Buffer
	for _, line := range lines {
		buffer.WriteString(line)
		buffer.WriteByte('\n')
	}
	return os.WriteFile(path, buffer.Bytes(), mode)
}

func linkServiceDefinitions() error {
	sourceDir, err := serviceDefinitionsDir()
	if err != nil {
		return err
	}
	entries, err := os.ReadDir(sourceDir)
	if err != nil {
		return err
	}
	for _, entry := range entries {
		if entry.IsDir() || filepath.Ext(entry.Name()) != ".toml" {
			continue
		}
		sourcePath := filepath.Join(sourceDir, entry.Name())
		targetPath := filepath.Join(workspaceServicesDir, entry.Name())
		if err := os.Remove(targetPath); err != nil && !errors.Is(err, os.ErrNotExist) {
			return err
		}
		if err := os.Symlink(sourcePath, targetPath); err != nil {
			return err
		}
		if err := os.Lchown(targetPath, agentUID, agentGID); err != nil {
			return err
		}
	}
	return nil
}

func serviceDefinitionsDir() (string, error) {
	candidates := make([]string, 0, 3)
	if workspace := os.Getenv("PWN_WORKSPACE"); workspace != "" {
		candidates = append(candidates, filepath.Join(workspace, "share", "workspace", "services"))
	}
	if len(os.Args) > 0 && filepath.IsAbs(os.Args[0]) {
		candidates = append(candidates, filepath.Join(filepath.Dir(os.Args[0]), "..", "share", "workspace", "services"))
	}
	executable, err := os.Executable()
	if err != nil {
		return "", err
	}
	candidates = append(candidates, filepath.Join(filepath.Dir(executable), "..", "share", "workspace", "services"))

	for _, candidate := range candidates {
		if _, err := os.Stat(candidate); err == nil {
			return candidate, nil
		} else if !errors.Is(err, os.ErrNotExist) {
			return "", err
		}
	}
	return "", fmt.Errorf("workspace service definitions not found in %v", candidates)
}

func writeFlag(flag string) error {
	if flag == "" {
		return errors.New("flag is empty")
	}
	if err := os.WriteFile("/flag", []byte(flag+"\n"), 0400); err != nil {
		return err
	}
	if err := os.Chown("/flag", 0, 0); err != nil {
		return err
	}
	return os.Chmod("/flag", 0400)
}

func runInit() error {
	if _, err := os.Stat("/challenge/.init"); errors.Is(err, os.ErrNotExist) {
		return nil
	} else if err != nil {
		return err
	}
	command := exec.Command("/challenge/.init")
	command.Stdout = os.Stderr
	command.Stderr = os.Stderr
	return command.Run()
}

func sendControl(writer *os.File, message controlMessage) {
	_ = json.NewEncoder(writer).Encode(message)
}
