# Workspace daemon

The workspace daemon is the node-local owner of workspace containers, the dedicated
workspace Docker network, workspace request proxying, and optional Btrfs home
volumes.

It always starts workspace containers with the `kata` runtime. It mounts `/nix`
read-only and runs the configured workspace runtime's `bin/workspace-entrypoint`.
The workspace agent listens on port 8000, so its readiness, exec, PTY, file, and
service APIs are available below `/w/<workspace-uuid>/`.

When `PWN_WORKSPACE_PUBLIC_KEY` is configured, `/api/` requests require the
Ed25519 signature headers implemented in `internal/http.go`. Without a public
key, signature verification is disabled. `/w/` uses the workspace UUID as its
access capability.

## Configuration

Required environment variables:

- `PWN_WORKSPACE_NIX_STORE_PATH` (host closure store mounted at `/nix/store` in workspaces)
- `PWN_WORKSPACE_PATH`
- `PWN_WORKSPACE_DOCKER_NETWORK`

Optional environment variables:

- `PWN_WORKSPACE_DAEMON_LISTEN_ADDRESS` (default `127.0.0.1:8000`)
- `PWN_WORKSPACE_AGENT_PORT` (default `8000`)
- `PWN_WORKSPACE_VOLUME_BASE_PATH`
- `PWN_WORKSPACE_PUBLIC_KEY` (hex-encoded raw Ed25519 public key)

If volume storage is configured, the path must be on a Btrfs filesystem mounted
`nosuid`. The local development host leaves it disabled because `pwnshop`
does not yet use persistent homes.

The Docker network must already exist as a labeled bridge network with exactly
one IPv4 subnet. The daemon derives its manual IPAM range from that subnet and
does not create or modify the network.

`PWN_WORKSPACE_NIX_STORE_PATH` contains only the Nix closure of
`PWN_WORKSPACE_PATH`. The host prepares this shared view once per runtime
generation, and every workspace receives it as one read-only bind at
`/nix/store`.

## Starting a workspace

`POST /api/workspaces/<workspace-uuid>/start` accepts:

```json
{
  "runtime_config": {
    "container_image_ref": "sha256:...",
    "entrypoint": ["/challenge/custom-init"],
    "env": {
      "PWN_FLAG": "pwn.college{...}",
      "PWN_USER": "hacker"
    }
  },
  "volume": {
    "volume_uuid": "00000000-0000-4000-8000-000000000000",
    "dst_path": "/home/hacker"
  }
}
```

`volume` is optional. `entrypoint` is an initialization command; when omitted,
the workspace runtime runs `/challenge/.init` if present. All workspaces receive
`CAP_SYS_PTRACE`, `CAP_SYS_ADMIN`, and `CAP_NET_ADMIN` inside their Kata VM.
