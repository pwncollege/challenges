package main

import (
	"context"
	"crypto/tls"
	"fmt"
	"log"
	"net"
	"net/http"
	"net/http/httputil"
	"strings"

	"github.com/miekg/dns"
)

type domainPolicy struct {
	patterns  []string
	exact     map[string]struct{}
	wildcards map[string]struct{}
}

func newDomainPolicy(patterns []string) (*domainPolicy, error) {
	policy := &domainPolicy{
		exact:     make(map[string]struct{}),
		wildcards: make(map[string]struct{}),
	}
	seen := make(map[string]struct{})
	for _, value := range patterns {
		pattern, wildcard, err := normalizePattern(value)
		if err != nil {
			return nil, fmt.Errorf("invalid egress domain %q: %w", value, err)
		}
		if _, duplicate := seen[pattern]; duplicate {
			return nil, fmt.Errorf("duplicate egress domain %q", pattern)
		}
		seen[pattern] = struct{}{}
		policy.patterns = append(policy.patterns, pattern)
		if wildcard {
			policy.wildcards[pattern] = struct{}{}
		} else {
			policy.exact[pattern] = struct{}{}
		}
	}
	return policy, nil
}

func normalizePattern(value string) (string, bool, error) {
	value = strings.ToLower(strings.TrimSuffix(value, "."))
	if strings.HasPrefix(value, "*.") {
		suffix, err := normalizeHost(strings.TrimPrefix(value, "*."))
		if err != nil {
			return "", false, err
		}
		if !strings.Contains(suffix, ".") {
			return "", false, fmt.Errorf("wildcard suffix must contain at least two labels")
		}
		return "*." + suffix, true, nil
	}
	if strings.Contains(value, "*") {
		return "", false, fmt.Errorf("wildcard must be the entire leftmost label")
	}
	host, err := normalizeHost(value)
	return host, false, err
}

func normalizeHost(value string) (string, error) {
	value = strings.ToLower(strings.TrimSuffix(value, "."))
	if value == "" || len(value) > 253 {
		return "", fmt.Errorf("invalid hostname length")
	}
	if net.ParseIP(value) != nil {
		return "", fmt.Errorf("IP addresses are not allowed")
	}
	for _, label := range strings.Split(value, ".") {
		if len(label) == 0 || len(label) > 63 || label[0] == '-' || label[len(label)-1] == '-' {
			return "", fmt.Errorf("invalid DNS label %q", label)
		}
		for _, character := range label {
			if (character < 'a' || character > 'z') && (character < '0' || character > '9') && character != '-' {
				return "", fmt.Errorf("invalid character in DNS label %q", label)
			}
		}
	}
	return value, nil
}

func (policy *domainPolicy) match(value string) (host, pattern string, ok bool) {
	host, err := normalizeHost(value)
	if err != nil {
		return "", "", false
	}
	if _, found := policy.exact[host]; found {
		return host, host, true
	}
	if firstDot := strings.IndexByte(host, '.'); firstDot > 0 {
		pattern := "*." + host[firstDot+1:]
		if _, found := policy.wildcards[pattern]; found {
			return host, pattern, true
		}
	}
	return "", "", false
}

func newDNSHandler(policy *domainPolicy, address net.IP) func(dns.ResponseWriter, *dns.Msg) {
	return func(writer dns.ResponseWriter, request *dns.Msg) {
		response := new(dns.Msg)
		response.SetReply(request)
		response.Authoritative = true
		if len(request.Question) != 1 || request.Question[0].Qclass != dns.ClassINET {
			response.Rcode = dns.RcodeFormatError
			_ = writer.WriteMsg(response)
			return
		}
		question := request.Question[0]
		if _, _, allowed := policy.match(question.Name); !allowed {
			response.Rcode = dns.RcodeNameError
		} else if question.Qtype == dns.TypeA {
			response.Answer = []dns.RR{&dns.A{
				Hdr: dns.RR_Header{Name: question.Name, Rrtype: dns.TypeA, Class: dns.ClassINET, Ttl: 60},
				A:   address,
			}}
		}
		_ = writer.WriteMsg(response)
	}
}

type upstreamHostKey struct{}

func newProxyHandler(scheme string, policy *domainPolicy, transport http.RoundTripper) http.Handler {
	if transport == nil {
		defaultTransport := http.DefaultTransport.(*http.Transport).Clone()
		defaultTransport.Proxy = nil
		defaultTransport.TLSClientConfig = &tls.Config{MinVersion: tls.VersionTLS12}
		transport = defaultTransport
	}
	proxy := &httputil.ReverseProxy{
		Director: func(request *http.Request) {
			host := request.Context().Value(upstreamHostKey{}).(string)
			request.URL.Scheme = scheme
			request.URL.Host = host
			request.Host = host
		},
		Transport: transport,
		ErrorHandler: func(writer http.ResponseWriter, _ *http.Request, err error) {
			log.Printf("egress proxy failed: %v", err)
			http.Error(writer, "egress proxy failed", http.StatusBadGateway)
		},
	}
	return http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		host, err := hostnameFromHostPort(request.Host)
		if err != nil {
			http.Error(writer, "host is not allowed", http.StatusForbidden)
			return
		}
		host, _, allowed := policy.match(host)
		if !allowed {
			http.Error(writer, "host is not allowed", http.StatusForbidden)
			return
		}
		if scheme == "https" {
			if request.TLS == nil {
				http.Error(writer, "TLS is required", http.StatusMisdirectedRequest)
				return
			}
			serverName, err := normalizeHost(request.TLS.ServerName)
			if err != nil || serverName != host {
				http.Error(writer, "host does not match TLS server name", http.StatusMisdirectedRequest)
				return
			}
		}
		request = request.WithContext(contextWithUpstreamHost(request, host))
		proxy.ServeHTTP(writer, request)
	})
}

func contextWithUpstreamHost(request *http.Request, host string) context.Context {
	return context.WithValue(request.Context(), upstreamHostKey{}, host)
}

func hostnameFromHostPort(value string) (string, error) {
	if host, _, err := net.SplitHostPort(value); err == nil {
		return host, nil
	}
	if strings.Contains(value, ":") {
		return "", fmt.Errorf("invalid host")
	}
	return value, nil
}
