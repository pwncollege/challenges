# Workspace daemon

The workspace daemon is the node-local owner of Kata workspaces, workspace
request proxying, and optional ext4 home images. It controls containerd through
CRI; containerd invokes the configured CNI chain for workspace networking.

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
- `PWN_WORKSPACE_CONTAINERD_ADDRESS`
- `PWN_WORKSPACE_EGRESS_ADDRESS`
- `PWN_WORKSPACE_LOG_DIRECTORY`
- `PWN_WORKSPACE_SECCOMP_PROFILE`

Optional environment variables:

- `PWN_WORKSPACE_DAEMON_LISTEN_ADDRESS` (default `127.0.0.1:8000`)
- `PWN_WORKSPACE_AGENT_PORT` (default `8000`)
- `PWN_WORKSPACE_VOLUME_BASE_PATH`
- `PWN_WORKSPACE_PUBLIC_KEY` (hex-encoded raw Ed25519 public key)

When volume storage is configured, the daemon creates sparse `home.ext4` files
under that directory. It registers them with `kata-runtime direct-volume`; QEMU
opens each file as a raw disk and the Kata agent mounts ext4 inside the guest with
`nosuid,nodev`. No host filesystem mount or loop device is used. The directory can
live on any host filesystem supporting ordinary sparse files. The platform puts
`mkfs.ext4` and `kata-runtime` on the daemon's PATH and enables Kata block devices.

`max_size_bytes` sets the image size, including filesystem metadata. New homes are
owned by UID/GID 1000. Snapshots contain complete zstd-compressed ext4 images. A
move stops the VM and releases its disk before capture; live backups would need
an explicit guest freeze or a storage snapshot mechanism. They are not implemented.
Compression finishes into a local immutable file before upload, giving HTTP a
known Content-Length. Restore checks the decompressed size and preserves holes
for zero-filled chunks. Retired images and cached snapshots remain until volume
deletion; automatic cache eviction is not implemented.

The platform generates a CNI bridge configuration. CNI `host-local` IPAM assigns
addresses from the platform's configured workspace subnet; the daemon reads the
assigned address from CRI sandbox status and does not know about the bridge or
subnet itself.

Workspace forwarding is denied by default. Sandboxes use the platform egress
service as their only DNS server; it currently resolves only `example.com` and
reverse proxies HTTP and HTTPS traffic for that name from the host network.

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
    "dst_path": "/home/hacker",
    "max_size_bytes": 1073741824,
    "snapshot": null
  }
}
```

`volume` is optional. `entrypoint` is an initialization command; when omitted,
the workspace runtime runs `/challenge/.init` if present. All workspaces receive
`CAP_SYS_PTRACE`, `CAP_SYS_ADMIN`, and `CAP_NET_ADMIN` inside their Kata VM.
Environment variables are opaque runtime configuration. `PWN_FLAG` is optional;
when present, the workspace runtime writes it to `/flag`.


The node reuses an active local home. If none exists, it downloads the supplied
`snapshot: {"snapshot_uuid": "...", "download_url": "..."}` (or uses that exact
cached snapshot). `snapshot: null` creates an empty home. A failed download fails
the start. An optional `replace_workspace_uuid` stops the previous workspace on
this node in the same command, after validating the request and image.

## Moving a home

`POST /api/volumes/<volume-uuid>/snapshots/<snapshot-uuid>/export` accepts:

```json
{
  "stop_workspace_uuid": "11111111-1111-4111-8111-111111111111",
  "upload_url": "https://control.example/api/volumes/..."
}
```

`stop_workspace_uuid` is optional when the home is already stopped. Export stops
the workspace, captures the snapshot, retires the writable home, and uploads the
snapshot. Any failure blocks movement. The node waits for the upload to complete before acknowledging export; the
coordinator then starts the destination. Retired copies are never reused as active homes.
Ordinary workspace stop retains the active home for the next local start.
`POST /api/volumes/<volume-uuid>/delete` removes an unattached volume and its caches.

## Retries and interrupted operations

Composite commands lock their workspaces and home; overlapping commands return
`423 resource_locked`. Workspace UUIDs identify one lifetime. Matching successful
starts return the running workspace without rerunning initialization. Different
parameters conflict. A stopped UUID cannot be started again.

Snapshot UUIDs identify one export. Repeating an export reuses its captured data;
a delayed retry cannot retire a newer home. Signed transfer URLs may be refreshed
without changing either command's identity.

Request records and stop/launch markers live in `PWN_WORKSPACE_LOG_DIRECTORY`,
which the platform places on persistent storage. Export records live beside the
home. Keep these records when restarting the daemon. An uncertain launch is
blocked for reconciliation if the running container cannot be confirmed; it is
never automatically rerun. The coordinator must retain its D1 claim until it has
confirmed the outcome. There is no automatic recovery scheduler.
