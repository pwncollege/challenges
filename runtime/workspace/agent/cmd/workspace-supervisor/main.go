package main

import (
	"log/slog"
	"os"
	"os/signal"
	"strconv"
	"syscall"
)

func main() {
	logger := slog.New(slog.NewTextHandler(os.Stderr, nil))
	agentPIDValue := os.Getenv("WORKSPACE_AGENT_PID")
	if agentPIDValue == "" {
		logger.Error("WORKSPACE_AGENT_PID is not set")
		os.Exit(2)
	}
	agentPID, err := strconv.Atoi(agentPIDValue)
	if err != nil || agentPID <= 0 {
		logger.Error("invalid agent pid", "pid", agentPIDValue)
		os.Exit(2)
	}

	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM, syscall.SIGCHLD)
	defer signal.Stop(signals)

	for {
		if code, done := reapChildren(agentPID); done {
			os.Exit(code)
		}

		signal := <-signals
		switch signal {
		case syscall.SIGINT, syscall.SIGTERM:
			logger.Info("stopping workspace agent", "signal", signal.String())
			_ = syscall.Kill(-agentPID, signal.(syscall.Signal))
		case syscall.SIGCHLD:
		}
	}
}

func reapChildren(agentPID int) (int, bool) {
	for {
		var status syscall.WaitStatus
		pid, err := syscall.Wait4(-1, &status, syscall.WNOHANG, nil)
		if pid <= 0 || err != nil {
			return 0, false
		}
		if pid == agentPID {
			return exitCode(status), true
		}
	}
}

func exitCode(status syscall.WaitStatus) int {
	if status.Exited() {
		return status.ExitStatus()
	}
	if status.Signaled() {
		return 128 + int(status.Signal())
	}
	return 1
}
