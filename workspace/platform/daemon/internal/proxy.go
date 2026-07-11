package daemon

import (
	"context"
	"errors"
	"io"
	"net"
	"net/http"
	"net/http/httputil"
	"net/netip"
	"net/url"
	"syscall"
	"time"
)

func (s *Server) handleWorkspaceProxy(w http.ResponseWriter, r *http.Request) {
	workspaceUUID := r.PathValue("workspaceUUID")
	proxyPath := "/"
	if path := r.PathValue("proxyPath"); path != "" {
		proxyPath += path
	}
	value, ok := s.proxies.Load(workspaceUUID)
	if !ok {
		jsonError(w, http.StatusNotFound, "workspace_not_found", "Workspace not found")
		return
	}
	ip := value.(netip.Addr)
	remote, _ := url.Parse(agentBaseURL(ip, s.config.agentPort))
	proxy := &httputil.ReverseProxy{
		Rewrite: func(req *httputil.ProxyRequest) {
			req.SetURL(remote)
			req.Out.URL.Path = proxyPath
			req.Out.URL.RawPath = ""
			req.Out.URL.RawQuery = req.In.URL.RawQuery
		},
	}
	proxy.ErrorHandler = func(w http.ResponseWriter, _ *http.Request, err error) {
		status, code, message := workspaceProxyError(err)
		jsonError(w, status, code, message)
	}
	proxy.ServeHTTP(w, r)
}

func workspaceProxyError(err error) (int, string, string) {
	var netErr net.Error
	switch {
	case errors.Is(err, context.Canceled):
		return 499, "client_canceled", "Client canceled request"
	case errors.Is(err, context.DeadlineExceeded), errors.As(err, &netErr) && netErr.Timeout():
		return http.StatusGatewayTimeout, "workspace_agent_timeout", "Workspace agent timed out"
	case errors.Is(err, syscall.ECONNREFUSED):
		return http.StatusBadGateway, "workspace_agent_unreachable", "Workspace agent refused connection"
	case errors.Is(err, syscall.ECONNRESET), errors.Is(err, syscall.EPIPE), errors.Is(err, syscall.ECONNABORTED):
		return http.StatusBadGateway, "workspace_agent_connection_lost", "Workspace agent connection lost"
	case errors.Is(err, syscall.ENETUNREACH), errors.Is(err, syscall.EHOSTUNREACH):
		return http.StatusBadGateway, "workspace_agent_network_unreachable", "Workspace agent network unreachable"
	default:
		return http.StatusBadGateway, "workspace_agent_unreachable", "Workspace agent unreachable"
	}
}

func waitForAgent(ctx context.Context, ip netip.Addr, port uint16) error {
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()
	healthURL := agentBaseURL(ip, port) + "/health"
	client := &http.Client{Timeout: time.Second}
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()
	for {
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, healthURL, nil)
		if err != nil {
			return err
		}
		resp, err := client.Do(req)
		if err == nil {
			_, _ = io.Copy(io.Discard, resp.Body)
			_ = resp.Body.Close()
			if resp.StatusCode >= 200 && resp.StatusCode < 300 {
				return nil
			}
		}
		select {
		case <-ctx.Done():
			return errors.New("workspace_agent_unreachable")
		case <-ticker.C:
		}
	}
}

func agentBaseURL(ip netip.Addr, port uint16) string {
	return "http://" + netip.AddrPortFrom(ip, port).String()
}
