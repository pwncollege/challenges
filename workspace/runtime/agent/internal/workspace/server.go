package workspace

import (
	"context"
	"errors"
	"html/template"
	"log/slog"
	"net"
	"net/http"
	"os"
	"time"
)

const defaultControlFD = 3

type agent struct {
	logger   *slog.Logger
	ready    *readiness
	services *serviceManager
}

func newAgent(logger *slog.Logger) *agent {
	return &agent{
		logger:   logger,
		ready:    newReadiness(),
		services: newServiceManager(logger),
	}
}

func RunAgent(ctx context.Context) error {
	logger := slog.New(slog.NewTextHandler(os.Stderr, nil))
	agent := newAgent(logger)
	go watchControl(ctx, logger, agent.ready, defaultControlFD)
	defer agent.services.stopAll()

	addr := ":" + envString("WORKSPACE_PORT", "8000")
	if host := os.Getenv("WORKSPACE_HOST"); host != "" {
		addr = host + addr
	}

	server := &http.Server{
		Addr:              addr,
		Handler:           agent.routes(),
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       10 * time.Second,
		IdleTimeout:       60 * time.Second,
	}

	listener, err := net.Listen("tcp", addr)
	if err != nil {
		logger.Error("failed to listen", "err", err)
		return err
	}

	go func() {
		logger.Info("starting workspace server", "addr", addr)
		if err := server.Serve(listener); err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Error("workspace server failed", "err", err)
			os.Exit(1)
		}
	}()

	<-ctx.Done()
	shutdownCtx, cancel := context.WithTimeout(context.Background(), envDuration("WORKSPACE_SHUTDOWN_TIMEOUT", 5*time.Second))
	defer cancel()
	return server.Shutdown(shutdownCtx)
}

func (a *agent) routes() *http.ServeMux {
	mux := http.NewServeMux()
	a.handle(mux, "/{$}", a.index)
	a.handle(mux, "/health", a.ok)
	a.handleReady(mux, "/ready", a.ok)
	a.handleReady(mux, "/pty/", a.ptySocket())
	a.handleReady(mux, "/exec/", a.execHandler())
	a.handleReady(mux, "/file/", a.fileHandler())
	a.handleReady(mux, "/service/", a.serviceHandler())
	return mux
}

func (a *agent) handle(mux *http.ServeMux, pattern string, handler http.HandlerFunc) {
	mux.HandleFunc(pattern, handler)
}

func (a *agent) handleReady(mux *http.ServeMux, pattern string, handler http.HandlerFunc) {
	a.handle(mux, pattern, a.ready.guard(handler))
}

func (a *agent) ok(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte("OK\n"))
}

func (a *agent) index(w http.ResponseWriter, _ *http.Request) {
	services, err := a.services.availableDefinitions()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	_ = indexTemplate.Execute(w, struct {
		Services []serviceDefinition
	}{
		Services: services,
	})
}

var indexTemplate = template.Must(template.New("index").Parse(`<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Workspace</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; max-width: 36rem; }
    h1 { font-size: 1.5rem; }
    ul { padding-left: 1.25rem; }
    li { margin: 0.5rem 0; }
  </style>
</head>
<body>
  <h1>Workspace</h1>
  <ul>
    {{range .Services -}}
    <li><a href="/service/{{.Name}}/">{{.Name}}</a></li>
    {{end -}}
  </ul>
</body>
</html>
`))
