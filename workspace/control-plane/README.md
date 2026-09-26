# Workspace control plane

This Cloudflare Worker coordinates users, workspace nodes, and home volumes. It
stores authoritative state in D1 and compressed ext4 home snapshots in R2. Workspace
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
- `SnapshotStore` owns R2 reads, streamed uploads, and signed transfer URLs.

Service constructors create lazy adapters without doing I/O, and are bound to each
request's environment. Tests can substitute services through Layers. Runtime
configuration, daemon error responses, and NDJSON progress events have shared
Effect schemas; their TypeScript types are derived from those definitions.

Workspace operations use `Effect.fn` and typed errors. Starts run under
`waitUntil` and emit a small number of NDJSON events. Disconnecting a reader does
not cancel the start or block it through stream backpressure. Start and stop mask
cooperative interruption through their final D1 update. Worker termination can
still interrupt an operation; its D1 claim remains held.

## Operation ownership

`workspace_operations` has one row per busy user. The user's workspace and home
share this claim. A start uses its new workspace UUID as the operation UUID. Its
plan records the chosen export snapshot UUID and home destination path; the
creating workspace records the target node and runtime configuration. The old
workspace and volume placement remain recorded until completion.

Fresh starts and same-node replacements send one node command. Moves send two:
source export (stop, capture, retire, upload), then destination start (prepare home,
start, wait for readiness). R2 transfer requests carry the data separately. The
successful path makes two D1 calls: an atomic claim batch and an atomic completion
batch. Every completion mutation checks claim ownership, releasing it last.

A confirmed preflight rejection can release an untouched start claim. Timeouts,
failed moves, uncertain starts/stops, and failed completion writes keep their
claims. Claims never expire automatically. Recovery must inspect the recorded
workspace and snapshot IDs, confirm source retirement, and reconcile the target
before completing or releasing a claim. This version has no automated reconciler.

Node retries use the same workspace/snapshot UUID and semantic parameters. A
running workspace is reused without rerunning initialization. Retired homes are
never reused; delayed exports cannot retire a newer home. Transfer URLs may be
refreshed. The Worker sends each command once.

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
containerd, Kata, the workspace daemon, and its network services. The daemon
creates sparse ext4 home images under `/var/lib/pwn.college/homes` and attaches
them directly to Kata. The normal development shell leaves home storage disabled.

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
with simulated node responses, including blocked export and destination failures. It also
covers request validation and disconnects during start and stop. Node-client tests verify signatures, typed errors,
malformed response handling, and transport cancellation using an injected fetch
implementation. Workflow tests can replace node commands with test services.

`npm run test:e2e` requires the development platform. It checks login, validation,
failed-start cleanup, the workspace proxy, and home persistence across replacement,
stop, and restart. It also repeats node start commands and checks that
they preserve home writes and do not rerun initialization. Set `PWN_WORKSPACE_DAEMON_URL` if the daemon uses another address.
Set `PWN_WORKSPACE_SECONDARY_DAEMON_URL` to also test moving a home to a second daemon
and back through R2. The second daemon needs its own home image directory and the
same signing key configuration; without it, that test is skipped.

Tests use disposable D1/R2 databases and clean up their workspaces and volumes.
`npm run dev` instead uses persisted local Worker storage; its seed step resets
workspace and operation records, so stop development workspaces before running it again.

## Current scope

Login deliberately accepts a seeded user UUID. This is a development control-plane
checkpoint, with production authentication and automatic recovery from interrupted
workflows still pending. Worker termination can leave operations claimed; recovery
must reconcile node state before releasing those claims.

Home movement must finish retiring the old writable home before the destination
starts. Nodes compress snapshots before upload, then send Content-Length. The
Worker streams each upload directly into R2 under its snapshot UUID, without
buffering multipart chunks or copying a staging object. R2 completes the write
before the upload response, and the node waits for that response before
acknowledging export.
Uploads still pass through the Worker and are subject to the Cloudflare plan’s
request body limit; large home exports need a direct R2 transfer path before
production use. Periodic backups are not scheduled by this version.
