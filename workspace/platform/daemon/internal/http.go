package daemon

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/google/uuid"
)

const maxAPIRequestBody = 1 << 20

func (s *Server) Serve() error {
	server := &http.Server{
		Addr:              s.config.listenAddress,
		Handler:           s.Handler(),
		ReadHeaderTimeout: 10 * time.Second,
		IdleTimeout:       90 * time.Second,
		MaxHeaderBytes:    32 << 10,
	}
	log.Printf("daemon listening on http://%s", s.config.listenAddress)
	return server.ListenAndServe()
}

func (s *Server) Handler() http.Handler {
	apiMux := http.NewServeMux()
	apiMux.HandleFunc("GET /api/health", s.handleHealth)

	apiMux.Handle("POST /api/workspaces/{workspaceUUID}/start", s.withUUID("workspaceUUID", s.withResourceLock("workspaceUUID", http.HandlerFunc(s.handleWorkspaceStart))))
	apiMux.Handle("POST /api/workspaces/{workspaceUUID}/stop", s.withUUID("workspaceUUID", s.withResourceLock("workspaceUUID", http.HandlerFunc(s.handleWorkspaceStop))))

	handleVolume := func(pattern string, handler http.HandlerFunc) {
		apiMux.Handle(pattern, s.withUUID("volumeUUID", s.withVolumeStorage(s.withResourceLock("volumeUUID", handler))))
	}
	handleVolume("POST /api/volumes/{volumeUUID}/snapshots/{snapshotUUID}/export", s.handleVolumeExport)
	handleVolume("POST /api/volumes/{volumeUUID}/delete", s.handleVolumeDelete)

	apiMux.HandleFunc("GET /api/container_images/list", s.handleImageList)
	apiMux.HandleFunc("POST /api/container_images/pull", s.handleImagePull)
	apiMux.HandleFunc("POST /api/container_images/remove", s.handleImageRemove)

	apiMux.HandleFunc("/api/", func(w http.ResponseWriter, r *http.Request) {
		jsonError(w, http.StatusNotFound, "not_found", "Route not found")
	})

	apiHandler := http.Handler(apiMux)
	if len(s.config.publicKey) > 0 {
		apiHandler = s.withSignatureVerification(apiHandler)
	}
	apiHandler = withRequestBodyLimit(apiHandler)

	mux := http.NewServeMux()
	mux.HandleFunc("GET /ping", handlePing)
	mux.Handle("/api/", apiHandler)
	mux.Handle("/w/{workspaceUUID}", s.withUUID("workspaceUUID", http.HandlerFunc(s.handleWorkspaceProxy)))
	mux.Handle("/w/{workspaceUUID}/{proxyPath...}", s.withUUID("workspaceUUID", http.HandlerFunc(s.handleWorkspaceProxy)))
	return mux
}

func withRequestBodyLimit(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.ContentLength > maxAPIRequestBody {
			jsonError(w, http.StatusRequestEntityTooLarge, "request_too_large", "Request body is too large")
			return
		}
		if r.Body != nil {
			r.Body = http.MaxBytesReader(w, r.Body, maxAPIRequestBody)
		}
		next.ServeHTTP(w, r)
	})
}

func handlePing(w http.ResponseWriter, _ *http.Request) {
	w.WriteHeader(http.StatusOK)
}

func (s *Server) withSignatureVerification(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		timestamp := r.Header.Get("X-Pwn-Workspace-Timestamp")
		signature := r.Header.Get("X-Pwn-Workspace-Signature")
		if timestamp == "" || signature == "" {
			jsonError(w, http.StatusUnauthorized, "invalid_signature", "Missing signature")
			return
		}
		parsedTS, err := strconv.ParseInt(timestamp, 10, 64)
		if err != nil || time.Since(time.Unix(parsedTS, 0)).Abs() > 5*time.Minute {
			jsonError(w, http.StatusForbidden, "expired_signature", "Expired signature")
			return
		}

		body := []byte{}
		if r.Body != nil && r.Method != http.MethodGet && r.Method != http.MethodHead {
			body, err = io.ReadAll(r.Body)
			if err != nil {
				requestBodyError(w, err)
				return
			}
			_ = r.Body.Close()
			r.Body = io.NopCloser(bytes.NewReader(body))
		}
		sum := sha256.Sum256(body)
		canonical := strings.Join([]string{
			r.Method,
			r.URL.RequestURI(),
			timestamp,
			hex.EncodeToString(sum[:]),
		}, "\n")
		sig, err := base64.StdEncoding.DecodeString(signature)
		if err != nil || !ed25519.Verify(s.config.publicKey, []byte(canonical), sig) {
			jsonError(w, http.StatusUnauthorized, "invalid_signature", "Invalid signature")
			return
		}
		next.ServeHTTP(w, r)
	})
}

func (s *Server) withUUID(parameter string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if _, err := uuid.Parse(r.PathValue(parameter)); err != nil {
			jsonError(w, http.StatusBadRequest, "invalid_request", "Invalid UUID")
			return
		}
		next.ServeHTTP(w, r)
	})
}

func (s *Server) withVolumeStorage(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if s.config.volumeBasePath == "" {
			jsonError(w, http.StatusServiceUnavailable, "volume_storage_unavailable", "Volume storage is not configured")
			return
		}
		next.ServeHTTP(w, r)
	})
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()
	if err := s.checkRuntimeReady(ctx, false); err != nil {
		jsonError(w, http.StatusServiceUnavailable, "unhealthy", err.Error())
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"healthy":                true,
		"volume_storage_enabled": s.config.volumeBasePath != "",
	})
}

func decodeJSON[T any](w http.ResponseWriter, r *http.Request) (T, bool) {
	var body T
	if r.Body == nil {
		return body, true
	}
	defer r.Body.Close()
	decoder := json.NewDecoder(r.Body)
	if err := decoder.Decode(&body); err != nil && err != io.EOF {
		requestBodyError(w, err)
		return body, false
	}
	return body, true
}

func requestBodyError(w http.ResponseWriter, err error) {
	var tooLarge *http.MaxBytesError
	if errors.As(err, &tooLarge) {
		jsonError(w, http.StatusRequestEntityTooLarge, "request_too_large", "Request body is too large")
		return
	}
	jsonError(w, http.StatusBadRequest, "invalid_request", "Invalid request")
}

func jsonError(w http.ResponseWriter, status int, code, message string) {
	writeJSON(w, status, map[string]any{"error": map[string]any{"code": code, "message": message}})
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("content-type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}

func (s *Server) withResourceLock(parameter string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		key := parameter + ":" + r.PathValue(parameter)
		if _, locked := s.resourceLocks.LoadOrStore(key, struct{}{}); locked {
			w.Header().Set("Retry-After", "1")
			jsonError(w, http.StatusLocked, "resource_locked", "Resource operation in progress")
			return
		}
		defer s.resourceLocks.Delete(key)
		next.ServeHTTP(w, r)
	})
}

// Composite commands acquire all their resources before changing any of them.
func (s *Server) lockResources(w http.ResponseWriter, keys ...string) (func(), bool) {
	held := []string{}
	release := func() {
		for _, key := range held {
			s.resourceLocks.Delete(key)
		}
	}
	for _, key := range keys {
		if strings.HasSuffix(key, ":") {
			continue
		}
		if _, locked := s.resourceLocks.LoadOrStore(key, struct{}{}); locked {
			release()
			jsonError(w, 423, "resource_locked", "Resource operation in progress")
			return nil, false
		}
		held = append(held, key)
	}
	return release, true
}
