package daemon

import (
	"bufio"
	"encoding/binary"
	"fmt"
	"io"
	"math/bits"
	"net/netip"
	"os"
	"strconv"
	"strings"
)

func (s *Server) validateWorkspaceRoutes() error {
	routes, err := os.Open("/proc/net/route")
	if err != nil {
		return fmt.Errorf("inspect host routes: %w", err)
	}
	defer routes.Close()
	return validateWorkspaceRoutes(s.config.workspaceSubnet, s.config.workspaceBridge, routes)
}

func validateWorkspaceRoutes(workspaceSubnet netip.Prefix, workspaceBridge string, routes io.Reader) error {
	scanner := bufio.NewScanner(routes)
	if !scanner.Scan() {
		return fmt.Errorf("inspect host routes: missing header")
	}
	for scanner.Scan() {
		fields := strings.Fields(scanner.Text())
		if len(fields) < 8 || fields[0] == workspaceBridge {
			continue
		}
		destination, err := parseProcRouteAddress(fields[1])
		if err != nil {
			return fmt.Errorf("inspect host route on %s: %w", fields[0], err)
		}
		mask, err := parseProcRouteAddress(fields[7])
		if err != nil {
			return fmt.Errorf("inspect host route mask on %s: %w", fields[0], err)
		}
		maskValue := binary.BigEndian.Uint32(mask.AsSlice())
		prefixBits := bits.OnesCount32(maskValue)
		if prefixBits == 0 {
			continue
		}
		if maskValue != ^uint32(0)<<uint(32-prefixBits) {
			return fmt.Errorf("inspect host route on %s: non-contiguous mask %s", fields[0], mask)
		}
		route := netip.PrefixFrom(destination, prefixBits).Masked()
		if route.Contains(workspaceSubnet.Addr()) || workspaceSubnet.Contains(route.Addr()) {
			return fmt.Errorf("workspace subnet %s overlaps host route %s on %s", workspaceSubnet, route, fields[0])
		}
	}
	if err := scanner.Err(); err != nil {
		return fmt.Errorf("inspect host routes: %w", err)
	}
	return nil
}

func parseProcRouteAddress(value string) (netip.Addr, error) {
	parsed, err := strconv.ParseUint(value, 16, 32)
	if err != nil {
		return netip.Addr{}, err
	}
	return netip.AddrFrom4([4]byte{
		byte(parsed),
		byte(parsed >> 8),
		byte(parsed >> 16),
		byte(parsed >> 24),
	}), nil
}
