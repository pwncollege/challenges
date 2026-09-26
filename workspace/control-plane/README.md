# Workspace control plane

This Cloudflare Worker coordinates users, workspace nodes, and home volumes. It
stores authoritative state in D1 and transferred Btrfs snapshots in R2. Workspace
containers themselves run on the node-level service in `../platform`.

## Effect

The Worker uses Effect **4.0.0-rc.117**, pinned to this release candidate. Effect's
`HttpRouter` handles routing and `Schema` validates request bodies; Hono and Zod
are no longer dependencies. `Environment` and `WorkerContext` provide bindings
per request. Three services separate workflows from external I/O:

- `NodeClient` signs commands, handles HTTP statuses, and validates daemon errors.
  Commands return success or a typed error; stopping an absent workspace succeeds.
  Mutating commands are sent once, with no automatic retries.
- `WorkspaceStore` owns D1 queries, claims, and state changes. The atomic SQL
  batches remain native D1 operations.
- `SnapshotStore` owns R2 reads, multipart uploads, commits, and signed transfer URLs.

Service constructors create lazy adapters without doing I/O, and are bound to each
request's environment. Tests can substitute services through Layers. Runtime
configuration, daemon error responses, and NDJSON progress events have shared
Effect schemas; their TypeScript types are derived from those definitions.

Workspace workflows use `Effect.fn` and typed errors. Scoped acquisitions register
rollback only after they succeed, then run cleanup in reverse order on failure.
The commit boundary masks interruption until D1 commits and the rollback scope
closes successfully, so a late cancellation cannot undo committed state or clear
another operation's claim. Cleanup failures are logged without skipping the
remaining finalizers.

Starts run under `waitUntil` and emit a small, bounded number of NDJSON events.
Disconnecting a reader does not cancel the start or hold its claim through stream
backpressure. Stops finish recording the node's response before accepting
interruption. These scopes handle cooperative cancellation; they do not provide
durable recovery if Cloudflare terminates the Worker.

The implementation follows the version-matched examples in `effect/ai-docs` and
the v4 documentation for [services](https://effect.website/docs/v4/requirements-management/services)
and [scopes](https://effect.website/docs/v4/resource-management/scope).

## Operation ownership

`workspace_operations` has one row per busy user: an operation UUID, kind, and
creation time. The home belongs to exactly one user, so the same claim covers
both workspace and home changes. A start uses its new workspace UUID as the
operation UUID; a stop generates one. Claim acquisition and related state changes
use an atomic D1 batch. Completion and rollback statements check both the user and
operation UUID, then release the claim last. Claims do not expire automatically.

Node starts with the same UUID and parameters reuse a running workspace. An
activation carries the operation UUID as `activation_uuid`; repeating it preserves
the writable home. Different start parameters or activation identities conflict.
These commands support retries while the coordinator owns the claim. The Worker
currently sends each command once; autonomous replay and recovery require a
persisted execution plan and reconciliation of uncertain node outcomes.

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
claim contention, stale completion/cleanup, rejected starts, streamed snapshot uploads, and home movement
with simulated node responses, including cleanup and activation failures. It also
covers request validation, disconnects, rollback ordering, and interruption
during acquisition and commit. Node-client tests verify signatures, typed errors,
malformed response handling, and transport cancellation using an injected fetch
implementation. Workflow tests can replace node commands with test services.

`npm run test:e2e` requires the development platform. It checks login, validation,
failed-start cleanup, the workspace proxy, and home persistence across replacement,
stop, and restart. It also repeats node start/activation commands and checks that
they preserve home writes and do not rerun initialization. Set `PWN_WORKSPACE_DAEMON_URL` if the daemon uses another address.
Set `PWN_WORKSPACE_SECONDARY_DAEMON_URL` to also test moving a home to a second daemon
and back through R2. The second daemon needs its own Btrfs volume directory and the
same signing key configuration; without it, that test is skipped.

Tests use disposable D1/R2 databases and clean up their workspaces and volumes.
`npm run dev` instead uses persisted local Worker storage; its seed step resets
workspace and operation records, so stop development workspaces before running it again.

## Current scope

Login deliberately accepts a seeded user UUID. This is a development control-plane
checkpoint, with production authentication and automatic recovery from interrupted
workflows still pending. Worker termination can leave operations claimed; recovery
must reconcile node state before releasing those claims.

Home movement stops the old workspace, saves its snapshot to R2, and then activates
the destination. Failure to remove the old active volume is logged and does not
block movement; the next activation on that node removes the stale copy first.
Snapshot uploads buffer at most one 5 MiB R2 part at a time, in addition to the
incoming stream chunk.
