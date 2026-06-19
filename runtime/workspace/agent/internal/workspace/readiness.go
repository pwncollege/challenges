package workspace

import (
	"context"
	"encoding/json"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"sync/atomic"
)

type controlMessage struct {
	Type    string `json:"type"`
	Message string `json:"message,omitempty"`
}

type readiness struct {
	state  atomic.Value
	done   chan struct{}
	closed atomic.Bool
}

type readinessState struct {
	status  string
	message string
}

func newReadiness() *readiness {
	ready := &readiness{
		done: make(chan struct{}),
	}
	ready.state.Store(readinessState{status: "initializing"})
	return ready
}

func (r *readiness) set(status string, message string) {
	r.state.Store(readinessState{status: status, message: message})
	if r.closed.CompareAndSwap(false, true) {
		close(r.done)
	}
}

func (r *readiness) load() readinessState {
	return r.state.Load().(readinessState)
}

func (r *readiness) wait(ctx context.Context) error {
	state := r.load()
	switch state.status {
	case "ready":
		return nil
	case "failed":
		return errors.New(failureMessage(state))
	}
	select {
	case <-r.done:
	case <-ctx.Done():
		return ctx.Err()
	}
	state = r.load()
	if state.status == "ready" {
		return nil
	}
	return errors.New(failureMessage(state))
}

func (r *readiness) guard(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, request *http.Request) {
		if err := r.wait(request.Context()); err != nil {
			http.Error(w, err.Error(), http.StatusServiceUnavailable)
			return
		}
		next(w, request)
	}
}

func failureMessage(state readinessState) string {
	if state.message != "" {
		return state.message
	}
	if state.status != "" {
		return state.status
	}
	return "workspace setup failed"
}

func watchControl(ctx context.Context, logger *slog.Logger, ready *readiness, fd int) {
	control := os.NewFile(uintptr(fd), "workspace-control")
	if control == nil {
		ready.set("failed", "workspace control pipe is unavailable")
		return
	}
	defer control.Close()
	message := controlMessage{}
	err := json.NewDecoder(control).Decode(&message)
	if err != nil {
		select {
		case <-ctx.Done():
			return
		default:
		}
		logger.Warn("workspace control pipe failed", "err", err)
		ready.set("failed", "workspace control pipe failed")
		return
	}
	switch message.Type {
	case "ready":
		ready.set("ready", "")
	case "failed":
		if message.Message == "" {
			message.Message = "workspace setup failed"
		}
		ready.set("failed", message.Message)
	default:
		ready.set("failed", "workspace control pipe sent an unknown message")
	}
}
