package main

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"io"
	"math/big"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/miekg/dns"
)

func TestDomainPolicy(t *testing.T) {
	policy := mustPolicy(t, "example.com", "*.example.net")
	for _, host := range []string{"example.com", "EXAMPLE.COM.", "api.example.net"} {
		if _, _, allowed := policy.match(host); !allowed {
			t.Errorf("%q was not allowed", host)
		}
	}
	for _, host := range []string{"www.example.com", "example.net", "a.b.example.net", "example.org", "192.0.2.1"} {
		if _, _, allowed := policy.match(host); allowed {
			t.Errorf("%q was allowed", host)
		}
	}
	for _, pattern := range []string{"", "*example.com", "foo.*.example.com", "*.com", "bad_name.example"} {
		if _, err := newDomainPolicy([]string{pattern}); err == nil {
			t.Errorf("invalid pattern %q was accepted", pattern)
		}
	}
	if _, err := newDomainPolicy([]string{"example.com", "EXAMPLE.COM."}); err == nil {
		t.Error("duplicate patterns were accepted")
	}
	empty := mustPolicy(t)
	if _, _, allowed := empty.match("example.com"); allowed {
		t.Error("empty policy allowed a domain")
	}
}

func TestDNSHandler(t *testing.T) {
	handler := newDNSHandler(mustPolicy(t, "example.com", "*.example.net"), net.ParseIP("192.0.2.1"))

	for _, name := range []string{"example.com.", "api.example.net."} {
		allowed := exchangeDNS(t, handler, name, dns.TypeA)
		if allowed.Rcode != dns.RcodeSuccess || len(allowed.Answer) != 1 || allowed.Answer[0].(*dns.A).A.String() != "192.0.2.1" {
			t.Fatalf("allowed response for %s = %#v", name, allowed)
		}
	}
	unsupported := exchangeDNS(t, handler, "example.com.", dns.TypeAAAA)
	if unsupported.Rcode != dns.RcodeSuccess || len(unsupported.Answer) != 0 {
		t.Fatalf("unsupported response = %#v", unsupported)
	}
	for _, name := range []string{"www.example.com.", "a.b.example.net.", "example.org."} {
		blocked := exchangeDNS(t, handler, name, dns.TypeA)
		if blocked.Rcode != dns.RcodeNameError || len(blocked.Answer) != 0 {
			t.Fatalf("blocked response for %s = %#v", name, blocked)
		}
	}
}

func TestProxyPolicy(t *testing.T) {
	policy := mustPolicy(t, "example.com", "*.example.net")
	var upstreamURL, upstreamHost string
	transport := roundTripFunc(func(request *http.Request) (*http.Response, error) {
		upstreamURL = request.URL.String()
		upstreamHost = request.Host
		return &http.Response{
			StatusCode: http.StatusNoContent,
			Header:     make(http.Header),
			Body:       io.NopCloser(strings.NewReader("")),
		}, nil
	})
	handler := newProxyHandler("http", policy, transport)

	request := httptest.NewRequest(http.MethodGet, "http://192.0.2.1/path?value=1", nil)
	request.Host = "api.example.net"
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, request)
	if response.Code != http.StatusNoContent || upstreamURL != "http://api.example.net/path?value=1" || upstreamHost != "api.example.net" {
		t.Fatalf("proxy response=%d url=%q host=%q", response.Code, upstreamURL, upstreamHost)
	}

	blocked := httptest.NewRecorder()
	blockedRequest := httptest.NewRequest(http.MethodGet, "http://192.0.2.1/", nil)
	blockedRequest.Host = "forbidden.example"
	handler.ServeHTTP(blocked, blockedRequest)
	if blocked.Code != http.StatusForbidden {
		t.Fatalf("blocked status = %d", blocked.Code)
	}

	httpsHandler := newProxyHandler("https", policy, transport)
	mismatch := httptest.NewRecorder()
	mismatchRequest := httptest.NewRequest(http.MethodGet, "https://192.0.2.1/", nil)
	mismatchRequest.Host = "example.com"
	mismatchRequest.TLS = &tls.ConnectionState{ServerName: "api.example.net"}
	httpsHandler.ServeHTTP(mismatch, mismatchRequest)
	if mismatch.Code != http.StatusMisdirectedRequest {
		t.Fatalf("mismatched TLS status = %d", mismatch.Code)
	}
}

func TestGeneratedCertificates(t *testing.T) {
	caCertificate, caPrivateKey, ca := writeTestCA(t)
	policy := mustPolicy(t, "example.com", "*.example.net")
	tlsConfig, err := newServerTLSConfig(policy, caCertificate, caPrivateKey)
	if err != nil {
		t.Fatal(err)
	}
	for _, host := range []string{"example.com", "api.example.net"} {
		certificate, err := tlsConfig.GetCertificate(&tls.ClientHelloInfo{ServerName: host})
		if err != nil {
			t.Fatal(err)
		}
		roots := x509.NewCertPool()
		roots.AddCert(ca)
		if _, err := certificate.Leaf.Verify(x509.VerifyOptions{DNSName: host, Roots: roots}); err != nil {
			t.Fatalf("verify %s: %v", host, err)
		}
	}
	if _, err := tlsConfig.GetCertificate(&tls.ClientHelloInfo{ServerName: "a.b.example.net"}); err == nil {
		t.Error("certificate issued for disallowed name")
	}
	emptyTLSConfig, err := newServerTLSConfig(mustPolicy(t), caCertificate, caPrivateKey)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := emptyTLSConfig.GetCertificate(&tls.ClientHelloInfo{ServerName: "example.com"}); err == nil {
		t.Error("empty policy issued a certificate")
	}
}

func writeTestCA(t *testing.T) (certificatePath, privateKeyPath string, certificate *x509.Certificate) {
	t.Helper()
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	now := time.Now()
	template := &x509.Certificate{
		SerialNumber:          big.NewInt(1),
		Subject:               pkix.Name{CommonName: "test CA"},
		NotBefore:             now.Add(-time.Hour),
		NotAfter:              now.Add(24 * time.Hour),
		KeyUsage:              x509.KeyUsageCertSign,
		BasicConstraintsValid: true,
		IsCA:                  true,
	}
	der, err := x509.CreateCertificate(rand.Reader, template, template, &key.PublicKey, key)
	if err != nil {
		t.Fatal(err)
	}
	certificate, err = x509.ParseCertificate(der)
	if err != nil {
		t.Fatal(err)
	}
	keyDER, err := x509.MarshalPKCS8PrivateKey(key)
	if err != nil {
		t.Fatal(err)
	}
	directory := t.TempDir()
	certificatePath = filepath.Join(directory, "ca.pem")
	privateKeyPath = filepath.Join(directory, "ca-key.pem")
	if err := os.WriteFile(certificatePath, pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der}), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(privateKeyPath, pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: keyDER}), 0600); err != nil {
		t.Fatal(err)
	}
	return certificatePath, privateKeyPath, certificate
}

func mustPolicy(t *testing.T, patterns ...string) *domainPolicy {
	t.Helper()
	policy, err := newDomainPolicy(patterns)
	if err != nil {
		t.Fatal(err)
	}
	return policy
}

func exchangeDNS(t *testing.T, handler func(dns.ResponseWriter, *dns.Msg), name string, questionType uint16) *dns.Msg {
	t.Helper()
	request := new(dns.Msg)
	request.SetQuestion(name, questionType)
	writer := &dnsRecorder{}
	handler(writer, request)
	if writer.message == nil {
		t.Fatal("DNS handler did not write a response")
	}
	return writer.message
}

type roundTripFunc func(*http.Request) (*http.Response, error)

func (function roundTripFunc) RoundTrip(request *http.Request) (*http.Response, error) {
	return function(request)
}

type dnsRecorder struct {
	message *dns.Msg
}

func (writer *dnsRecorder) WriteMsg(message *dns.Msg) error { writer.message = message; return nil }
func (writer *dnsRecorder) Write(data []byte) (int, error)  { return len(data), nil }
func (writer *dnsRecorder) Close() error                    { return nil }
func (writer *dnsRecorder) TsigStatus() error               { return nil }
func (writer *dnsRecorder) TsigTimersOnly(bool)             {}
func (writer *dnsRecorder) Hijack()                         {}
func (writer *dnsRecorder) LocalAddr() net.Addr             { return &net.UDPAddr{} }
func (writer *dnsRecorder) RemoteAddr() net.Addr            { return &net.UDPAddr{} }
