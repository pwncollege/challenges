package daemon

import (
	"net/netip"
	"strings"
	"testing"
)

func TestValidateWorkspaceRoutes(t *testing.T) {
	const header = "Iface Destination Gateway Flags RefCnt Use Metric Mask MTU Window IRTT\n"
	tests := []struct {
		name    string
		routes  string
		wantErr bool
	}{
		{
			name:   "default and expected bridge",
			routes: "eth0 00000000 01020304 0003 0 0 0 00000000 0 0 0\npwn-workspace0 00001FAC 00000000 0001 0 0 0 00F0FFFF 0 0 0\n",
		},
		{
			name:    "same subnet on another bridge",
			routes:  "br-old 00001FAC 00000000 0001 0 0 0 00F0FFFF 0 0 0\n",
			wantErr: true,
		},
		{
			name:    "more specific route",
			routes:  "eth1 00001FAC 00000000 0001 0 0 0 00FFFFFF 0 0 0\n",
			wantErr: true,
		},
		{
			name:   "unrelated route",
			routes: "eth1 0002A8C0 00000000 0001 0 0 0 00FFFFFF 0 0 0\n",
		},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			err := validateWorkspaceRoutes(
				netip.MustParsePrefix("172.31.0.0/20"),
				"pwn-workspace0",
				strings.NewReader(header+test.routes),
			)
			if (err != nil) != test.wantErr {
				t.Fatalf("error = %v, wantErr %v", err, test.wantErr)
			}
		})
	}
}
