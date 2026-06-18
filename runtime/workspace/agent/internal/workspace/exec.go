package workspace

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"os"
	"os/exec"
	"syscall"
	"time"
)

const timeoutExitCode = 124

type execRequest struct {
	Argv    []string          `json:"argv"`
	Cwd     string            `json:"cwd,omitempty"`
	Env     map[string]string `json:"env,omitempty"`
	Stdin   string            `json:"stdin,omitempty"`
	Timeout float64           `json:"timeout,omitempty"`
}

type execResponse struct {
	ExitCode int    `json:"exit_code"`
	Stdout   string `json:"stdout"`
	Stderr   string `json:"stderr"`
}

func (a *agent) execHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			w.Header().Set("Allow", http.MethodPost)
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}

		var request execRequest
		if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		if len(request.Argv) == 0 || request.Argv[0] == "" {
			http.Error(w, "argv must not be empty", http.StatusBadRequest)
			return
		}
		if request.Timeout < 0 {
			http.Error(w, "timeout must not be negative", http.StatusBadRequest)
			return
		}

		ctx := r.Context()
		cancel := func() {}
		if request.Timeout > 0 {
			ctx, cancel = context.WithTimeout(ctx, time.Duration(request.Timeout*float64(time.Second)))
		}
		defer cancel()

		command := exec.CommandContext(ctx, request.Argv[0], request.Argv[1:]...)
		command.Dir = request.Cwd
		command.Env = execEnv(request.Env)
		command.Stdin = bytes.NewBufferString(request.Stdin)
		command.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
		command.Cancel = func() error {
			killProcessGroup(command)
			return nil
		}
		command.WaitDelay = 1 * time.Second

		var stdout bytes.Buffer
		var stderr bytes.Buffer
		command.Stdout = &stdout
		command.Stderr = &stderr

		err := command.Run()
		exitCode := 0
		if errors.Is(ctx.Err(), context.DeadlineExceeded) {
			exitCode = timeoutExitCode
		} else if err != nil {
			var exitErr *exec.ExitError
			if errors.As(err, &exitErr) {
				exitCode = exitErr.ExitCode()
			} else if errors.Is(err, exec.ErrWaitDelay) {
				exitCode = 0
			} else {
				httpError(w, err)
				return
			}
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_ = json.NewEncoder(w).Encode(execResponse{
			ExitCode: exitCode,
			Stdout:   stdout.String(),
			Stderr:   stderr.String(),
		})
	}
}

func execEnv(overrides map[string]string) []string {
	env := os.Environ()
	for name, value := range overrides {
		env = append(env, name+"="+value)
	}
	return env
}
