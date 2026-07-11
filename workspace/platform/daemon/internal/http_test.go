package daemon

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"io"
	"net/http"
	"net/http/httptest"
	"strconv"
	"testing"
	"time"
)

func TestSignatureVerificationPreservesBody(t *testing.T) {
	publicKey, privateKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	s := &Server{config: Config{publicKey: publicKey}}
	wantBody := []byte(`{"hello":"workspace"}`)
	wrapped := s.withSignatureVerification(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, err := io.ReadAll(r.Body)
		if err != nil {
			t.Error(err)
		}
		if !bytes.Equal(body, wantBody) {
			t.Errorf("body = %q, want %q", body, wantBody)
		}
		w.WriteHeader(http.StatusNoContent)
	}))

	request := signedRequest(t, privateKey, http.MethodPost, "/api/test?value=1", wantBody, time.Now())
	response := httptest.NewRecorder()
	wrapped.ServeHTTP(response, request)
	if response.Code != http.StatusNoContent {
		t.Fatalf("status = %d, want %d: %s", response.Code, http.StatusNoContent, response.Body.String())
	}
}

func TestAPIWithoutPublicKeyDoesNotRequireSignature(t *testing.T) {
	s := &Server{}
	request := httptest.NewRequest(http.MethodGet, "/api/unknown", nil)
	response := httptest.NewRecorder()
	s.Handler().ServeHTTP(response, request)
	if response.Code != http.StatusNotFound {
		t.Fatalf("status = %d, want %d: %s", response.Code, http.StatusNotFound, response.Body.String())
	}
}

func TestSignatureVerificationRejectsExpiredAndChangedRequests(t *testing.T) {
	publicKey, privateKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	s := &Server{config: Config{publicKey: publicKey}}
	wrapped := s.withSignatureVerification(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusNoContent)
	}))

	tests := []struct {
		name       string
		request    *http.Request
		wantStatus int
	}{
		{
			name:       "expired",
			request:    signedRequest(t, privateKey, http.MethodGet, "/api/test", nil, time.Now().Add(-10*time.Minute)),
			wantStatus: http.StatusForbidden,
		},
		{
			name: "changed path",
			request: func() *http.Request {
				request := signedRequest(t, privateKey, http.MethodGet, "/api/test", nil, time.Now())
				request.URL.Path = "/api/other"
				return request
			}(),
			wantStatus: http.StatusUnauthorized,
		},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			response := httptest.NewRecorder()
			wrapped.ServeHTTP(response, test.request)
			if response.Code != test.wantStatus {
				t.Fatalf("status = %d, want %d: %s", response.Code, test.wantStatus, response.Body.String())
			}
		})
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
