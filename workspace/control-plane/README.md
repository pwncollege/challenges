# Workspace control plane

This Cloudflare Worker coordinates users, workspace nodes, and home volumes. It
stores authoritative state in D1 and transferred Btrfs snapshots in R2. Workspace
containers themselves run on the node-level service in `../platform`.

## Local development

From the repository root:

```console
$ nix develop .#control-plane
$ cd workspace/control-plane
$ npm ci
$ npm test
$ npm run dev
```

The development shell starts the real local workspace platform, including
containerd, Kata, the workspace daemon, and its network services. It also creates
a sparse Btrfs filesystem at `/var/lib/pwn.college/control-plane-volumes.img` and
mounts it with `nosuid` at `/var/lib/pwn.college/volumes`. The normal development
shell does not enable home volume storage.

Use `pwn-workspace-storage status` to inspect that mount or
`sudo pwn-workspace-storage teardown` to unmount it after stopping any workspaces.

The containerd CRI plugin uses its conventional internal `k8s.io` namespace. This
stack does not run Kubernetes or kubelet; the workspace daemon talks directly to
containerd, and images pulled through the daemon are stored in that namespace.

The local seed contains user `11111111-1111-4111-8111-111111111111` and node
`33333333-3333-4333-8333-333333333333`. The Worker listens on port 8787 and the
workspace daemon listens on port 8000.

The signing keys in `wrangler.toml` are local-development credentials. Production
deployments should provide their own Worker secrets and configure each node with
the matching raw Ed25519 public key.

## Tests

`npm test` runs TypeScript checks, local D1/R2 tests, and the real Kata workspace
lifecycle test. `npm run test:unit` runs without a workspace daemon: it covers
claim contention, rejected starts, streamed snapshot uploads, and home movement
with simulated node responses, including cleanup and activation failures.

`npm run test:e2e` requires the development platform. It checks login, validation,
failed-start cleanup, the workspace proxy, and home persistence across replacement,
stop, and restart. Set `PWN_WORKSPACE_DAEMON_URL` if the daemon uses another address.
Set `PWN_WORKSPACE_SECONDARY_DAEMON_URL` to also test moving a home to a second daemon
and back through R2. The second daemon needs its own Btrfs volume directory and the
same signing key configuration; without it, that test is skipped.

Tests use disposable D1/R2 databases and clean up their workspaces and volumes.
`npm run dev` instead uses persisted local Worker storage; its seed step resets
workspace and lock records, so stop development workspaces before running it again.

## Current scope

Login deliberately accepts a seeded user UUID. This is a development control-plane
checkpoint, with production authentication and automatic recovery from interrupted
workflows still pending. A Worker interruption can leave claims locked; recovery
must reconcile node state before clearing those locks.

Home movement stops the old workspace, saves its snapshot to R2, and then activates
the destination. Failure to remove the old active volume is logged and does not
block movement; the next activation on that node removes the stale copy first.
Snapshot uploads buffer at most one 5 MiB R2 part at a time, in addition to the
incoming stream chunk.
