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
	"sort"
	"strconv"
	"strings"
	"syscall"
)

const agentUID = 1000
const agentGID = 1000
const challengeBin = "/challenge/bin"
const challengeRunDir = "/run/challenge"
const challengeRunBin = "/run/challenge/bin"
const workspaceRunDir = "/run/workspace"
const workspaceProfile = "/run/workspace/profile"
const workspaceProfileBin = "/run/workspace/profile/bin"
const workspaceProfileScript = "/run/workspace/profile/etc/profile.d/99-pwn-workspace.sh"
const workspaceUserRunDir = "/run/workspace/user"
const workspaceServicesDir = "/run/workspace/user/services"
const systemProfileScript = "/etc/profile.d/99-pwn-workspace.sh"
const userShell = "/run/workspace/profile/bin/bash"

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
		"SHELL="+userShell,
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
	if err := setupRunDirectories(); err != nil {
		return err
	}
	if err := setupSystemEnvironment(); err != nil {
		return err
	}
	if err := setupUsers(config.user, config.home); err != nil {
		return err
	}
	if err := writeFlag(config.flag); err != nil {
		return fmt.Errorf("write flag: %w", err)
	}
	return nil
}

func setupRunDirectories() error {
	for _, directory := range []string{challengeRunDir, workspaceRunDir} {
		if err := os.MkdirAll(directory, 0755); err != nil {
			return err
		}
		if err := os.Chmod(directory, 0755); err != nil {
			return err
		}
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
	if err := linkChallengeBin(); err != nil {
		return err
	}
	if err := linkWorkspaceProfile(); err != nil {
		return err
	}
	return linkServiceDefinitions()
}

func linkChallengeBin() error {
	if _, err := os.Stat(challengeBin); errors.Is(err, os.ErrNotExist) {
		return nil
	} else if err != nil {
		return err
	}
	if err := os.Remove(challengeRunBin); err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}
	return os.Symlink(challengeBin, challengeRunBin)
}

func linkWorkspaceProfile() error {
	target, err := workspaceProfileTarget()
	if err != nil {
		return err
	}
	if err := os.Remove(workspaceProfile); err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}
	return os.Symlink(target, workspaceProfile)
}

func workspaceProfileTarget() (string, error) {
	if len(os.Args) > 0 && filepath.IsAbs(os.Args[0]) {
		return filepath.Clean(filepath.Join(filepath.Dir(os.Args[0]), "..")), nil
	}
	executable, err := os.Executable()
	if err != nil {
		return "", err
	}
	return filepath.Clean(filepath.Join(filepath.Dir(executable), "..")), nil
}

func setupSystemEnvironment() error {
	if err := ensureShell("/bin/sh", userShell); err != nil {
		return err
	}
	if err := os.MkdirAll("/etc/profile.d", 0755); err != nil {
		return err
	}
	if err := linkSystemBashrc(); err != nil {
		return err
	}
	os.Setenv("PATH", workspacePath(os.Getenv("PATH")))
	os.Setenv("LANG", "C.UTF-8")
	os.Setenv("MANPATH", filepath.Join(workspaceProfile, "share", "man")+":")
	os.Setenv("SSL_CERT_FILE", filepath.Join(workspaceProfile, "etc", "ssl", "certs", "ca-bundle.crt"))
	os.Setenv("TERMINFO", filepath.Join(workspaceProfile, "share", "terminfo"))
	if err := writeEnvironment(); err != nil {
		return err
	}
	return linkProfileScript()
}

func ensureShell(path string, target string) error {
	if _, err := os.Stat(path); err == nil {
		return nil
	} else if !errors.Is(err, os.ErrNotExist) {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return err
	}
	return os.Symlink(target, path)
}

func linkSystemBashrc() error {
	if _, err := os.Stat("/etc/bashrc"); err == nil {
		return nil
	} else if !errors.Is(err, os.ErrNotExist) {
		return err
	}
	if _, err := os.Stat("/etc/bash.bashrc"); errors.Is(err, os.ErrNotExist) {
		return nil
	} else if err != nil {
		return err
	}
	return os.Symlink("/etc/bash.bashrc", "/etc/bashrc")
}

func writeEnvironment() error {
	keys := []string{"PATH", "LANG", "MANPATH", "SSL_CERT_FILE", "TERMINFO"}
	var buffer bytes.Buffer
	for _, key := range keys {
		value := os.Getenv(key)
		if value == "" {
			continue
		}
		buffer.WriteString(key)
		buffer.WriteString("=")
		buffer.WriteString(strconv.Quote(value))
		buffer.WriteByte('\n')
	}
	return os.WriteFile("/etc/environment", buffer.Bytes(), 0644)
}

func linkProfileScript() error {
	if _, err := os.Stat(workspaceProfileScript); err != nil {
		return err
	}
	if err := os.Remove(systemProfileScript); err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}
	return os.Symlink(workspaceProfileScript, systemProfileScript)
}

func workspacePath(path string) string {
	prefix := challengeRunBin + ":" + workspaceProfileBin
	if path == prefix || strings.HasPrefix(path, prefix+":") {
		return path
	}
	if path == "" {
		return prefix
	}
	return prefix + ":" + path
}

func runChallengeInit() error {
	if err := runInit(); err != nil {
		return fmt.Errorf("run .init: %w", err)
	}
	return nil
}

func setupUsers(user string, home string) error {
	if err := upsertPasswdUsers(user, home); err != nil {
		return err
	}
	if err := upsertGroups(user); err != nil {
		return err
	}
	if err := setupHome("/root", 0, 0); err != nil {
		return err
	}
	if err := setupHome(home, agentUID, agentGID); err != nil {
		return err
	}
	return remountHomeNosuid(home)
}

func setupHome(home string, uid int, gid int) error {
	if _, err := os.Stat(home); errors.Is(err, os.ErrNotExist) {
		if err := os.MkdirAll(home, 0755); err != nil {
			return err
		}
	} else if err != nil {
		return err
	}
	return os.Chown(home, uid, gid)
}

type passwdEntry struct {
	fields []string
}

func upsertPasswdUsers(user string, home string) error {
	const passwdPath = "/etc/passwd"

	data, err := os.ReadFile(passwdPath)
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}

	entries := make([]passwdEntry, 0)
	seenRoot := false
	seenUser := false
	for _, line := range strings.Split(strings.TrimRight(string(data), "\n"), "\n") {
		if line == "" {
			continue
		}
		fields := strings.Split(line, ":")
		if len(fields) < 7 {
			continue
		}
		uid, validUID := parseID(fields[2])
		switch {
		case fields[0] == "root" || validUID && uid == 0:
			if seenRoot {
				continue
			}
			fields[0] = "root"
			fields[2] = "0"
			fields[3] = "0"
			fields[4] = "root"
			fields[5] = "/root"
			fields[6] = userShell
			seenRoot = true
		case fields[0] == user || validUID && uid == agentUID:
			if seenUser {
				continue
			}
			fields[0] = user
			fields[2] = strconv.Itoa(agentUID)
			fields[3] = strconv.Itoa(agentGID)
			fields[4] = user
			fields[5] = home
			fields[6] = userShell
			seenUser = true
		}
		entries = append(entries, passwdEntry{fields: fields})
	}
	if !seenRoot {
		entries = append(entries, passwdEntry{fields: []string{"root", "x", "0", "0", "root", "/root", userShell}})
	}
	if !seenUser {
		entries = append(entries, passwdEntry{fields: []string{user, "x", strconv.Itoa(agentUID), strconv.Itoa(agentGID), user, home, userShell}})
	}
	sort.SliceStable(entries, func(i int, j int) bool {
		return numericField(entries[i].fields, 2) < numericField(entries[j].fields, 2)
	})
	lines := make([]string, 0, len(entries))
	for _, entry := range entries {
		lines = append(lines, strings.Join(entry.fields, ":"))
	}
	return writeLines(passwdPath, lines, 0644)
}

type groupEntry struct {
	fields []string
}

func upsertGroups(user string) error {
	const groupPath = "/etc/group"

	data, err := os.ReadFile(groupPath)
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}

	entries := make([]groupEntry, 0)
	seenRoot := false
	seenUser := false
	for _, line := range strings.Split(strings.TrimRight(string(data), "\n"), "\n") {
		if line == "" {
			continue
		}
		fields := strings.Split(line, ":")
		if len(fields) < 4 {
			continue
		}
		gid, validGID := parseID(fields[2])
		switch {
		case fields[0] == "root" || validGID && gid == 0:
			if seenRoot {
				continue
			}
			fields[0] = "root"
			fields[2] = "0"
			seenRoot = true
		case fields[0] == user || validGID && gid == agentGID:
			if seenUser {
				continue
			}
			fields[0] = user
			fields[2] = strconv.Itoa(agentGID)
			seenUser = true
		}
		entries = append(entries, groupEntry{fields: fields})
	}
	if !seenRoot {
		entries = append(entries, groupEntry{fields: []string{"root", "x", "0", ""}})
	}
	if !seenUser {
		entries = append(entries, groupEntry{fields: []string{user, "x", strconv.Itoa(agentGID), ""}})
	}
	sort.SliceStable(entries, func(i int, j int) bool {
		return numericField(entries[i].fields, 2) < numericField(entries[j].fields, 2)
	})
	lines := make([]string, 0, len(entries))
	for _, entry := range entries {
		lines = append(lines, strings.Join(entry.fields, ":"))
	}
	return writeLines(groupPath, lines, 0644)
}

func numericField(fields []string, index int) int {
	if index >= len(fields) {
		return int(^uint(0) >> 1)
	}
	value, ok := parseID(fields[index])
	if !ok {
		return int(^uint(0) >> 1)
	}
	return value
}

func parseID(value string) (int, bool) {
	id, err := strconv.Atoi(value)
	return id, err == nil
}

func remountHomeNosuid(home string) error {
	mount, ok, err := findMount(home)
	if err != nil || !ok {
		return err
	}
	if containsMountOption(mount.options, "nosuid") {
		return nil
	}
	return syscall.Mount("", home, "", syscall.MS_REMOUNT|syscall.MS_NOSUID, "")
}

type mountInfo struct {
	mountpoint string
	options    string
}

func findMount(path string) (mountInfo, bool, error) {
	data, err := os.ReadFile("/proc/self/mountinfo")
	if err != nil {
		return mountInfo{}, false, err
	}
	for _, line := range strings.Split(strings.TrimRight(string(data), "\n"), "\n") {
		fields := strings.Fields(line)
		if len(fields) < 6 {
			continue
		}
		if unescapeMountPath(fields[4]) == path {
			return mountInfo{mountpoint: path, options: fields[5]}, true, nil
		}
	}
	return mountInfo{}, false, nil
}

func unescapeMountPath(path string) string {
	replacer := strings.NewReplacer(`\040`, " ", `\011`, "\t", `\012`, "\n", `\134`, `\`)
	return replacer.Replace(path)
}

func containsMountOption(options string, option string) bool {
	for _, current := range strings.Split(options, ",") {
		if current == option {
			return true
		}
	}
	return false
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
	directory := filepath.Join(workspaceProfile, "share", "workspace", "services")
	if _, err := os.Stat(directory); err != nil {
		return "", err
	}
	return directory, nil
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
