package main

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/miekg/dns"
)

type config struct {
	address       net.IP
	policy        *domainPolicy
	caCertificate string
	caPrivateKey  string
}

func main() {
	config, err := loadConfig()
	if err != nil {
		log.Fatal(err)
	}
	if err := serve(config); err != nil {
		log.Fatal(err)
	}
}

func loadConfig() (config, error) {
	address := net.ParseIP(os.Getenv("PWN_WORKSPACE_EGRESS_ADDRESS")).To4()
	if address == nil {
		return config{}, errors.New("PWN_WORKSPACE_EGRESS_ADDRESS must be an IPv4 address")
	}
	domainsPath := os.Getenv("PWN_WORKSPACE_EGRESS_DOMAINS_FILE")
	if domainsPath == "" {
		return config{}, errors.New("PWN_WORKSPACE_EGRESS_DOMAINS_FILE must not be empty")
	}
	domainsJSON, err := os.ReadFile(domainsPath)
	if err != nil {
		return config{}, fmt.Errorf("read egress domains: %w", err)
	}
	var domains []string
	if err := json.Unmarshal(domainsJSON, &domains); err != nil {
		return config{}, fmt.Errorf("parse egress domains: %w", err)
	}
	policy, err := newDomainPolicy(domains)
	if err != nil {
		return config{}, err
	}
	caCertificate := os.Getenv("PWN_WORKSPACE_EGRESS_CA_CERTIFICATE")
	caPrivateKey := os.Getenv("PWN_WORKSPACE_EGRESS_CA_PRIVATE_KEY")
	if caCertificate == "" || caPrivateKey == "" {
		return config{}, errors.New("egress CA certificate and private key must not be empty")
	}
	return config{
		address:       address,
		policy:        policy,
		caCertificate: caCertificate,
		caPrivateKey:  caPrivateKey,
	}, nil
}

func serve(config config) error {
	address := config.address.String()
	tlsConfig, err := newServerTLSConfig(config.policy, config.caCertificate, config.caPrivateKey)
	if err != nil {
		return err
	}
	httpsListener, err := tls.Listen("tcp", net.JoinHostPort(address, "443"), tlsConfig)
	if err != nil {
		return err
	}

	dnsHandler := dns.HandlerFunc(newDNSHandler(config.policy, config.address))
	dnsServers := []*dns.Server{
		{Addr: net.JoinHostPort(address, "53"), Net: "udp", Handler: dnsHandler},
		{Addr: net.JoinHostPort(address, "53"), Net: "tcp", Handler: dnsHandler},
	}
	httpServers := []*http.Server{
		newHTTPServer(net.JoinHostPort(address, "80"), newProxyHandler("http", config.policy, nil)),
		newHTTPServer("", newProxyHandler("https", config.policy, nil)),
	}

	serverErrors := make(chan error, len(dnsServers)+len(httpServers))
	for _, server := range dnsServers {
		go func() { serverErrors <- server.ListenAndServe() }()
	}
	go func() { serverErrors <- httpServers[0].ListenAndServe() }()
	go func() { serverErrors <- httpServers[1].Serve(httpsListener) }()

	log.Printf("workspace egress serving %v through %s", config.policy.patterns, address)
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	var serveErr error
	select {
	case <-ctx.Done():
	case err := <-serverErrors:
		if err != nil && !errors.Is(err, http.ErrServerClosed) {
			serveErr = err
		}
	}

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	for _, server := range dnsServers {
		_ = server.ShutdownContext(shutdownCtx)
	}
	for _, server := range httpServers {
		_ = server.Shutdown(shutdownCtx)
	}
	return serveErr
}

func newHTTPServer(address string, handler http.Handler) *http.Server {
	return &http.Server{
		Addr:              address,
		Handler:           handler,
		ReadHeaderTimeout: 10 * time.Second,
		IdleTimeout:       90 * time.Second,
		MaxHeaderBytes:    32 << 10,
	}
}
