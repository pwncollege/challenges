# Layered EROFS runtime tests

Start the node with `nix develop .#control-plane`. Container roots use shared
compressed EROFS layers and a separate 1 GiB tmpfs upper filesystem.
The workspace entrypoint mounts a separate 1 GiB tmpfs at `/tmp`.
There is no runtime storage backend selector.

Current load tests and historical comparisons are in [results](results/README.md).

## Local patches

- `firecracker-vmdk.patch` is derived from
  [upstream PR #5741](https://github.com/firecracker-microvm/firecracker/pull/5741)
  at `46a50761d890437bc38b9785fb878bd9494c95cc`, adapted to Firecracker 1.17.0.
  Drop it when upgrading to a version containing that PR.
- `kata-firecracker.patch` connects Kata's existing EROFS support to Firecracker:
  read-only VMDK slots, individual layer file mounts inside the jail, and cleanup.
  [Kata #12763](https://github.com/kata-containers/kata-containers/pull/12763)
  implemented the general EROFS/QEMU path and left Firecracker integration open.
- `kata-agent-erofs.patch` resolves Firecracker MMIO disks and rescans partitions
  after replacing a placeholder disk, and bounds the memory-backed upper to a
  separate 1 GiB tmpfs with tracked cleanup. Nix builds the patched static agent and
  installs it into the matching upstream guest image.
- `containerd-erofs.patch` translates the userspace EROFS reader's unsupported
  feature error into containerd's existing kernel-mount fallback. Regression
  tests cover compressed images and malformed-image errors.

## Correctness

Run `npm test` inside `workspace/control-plane` in the control-plane dev shell.
The E2E fixtures verify rootfs and tmpfs capacities, allocation failures at their
limits, nested KVM, egress, read-only Nix storage, replacement, and home persistence.
`PWN_WORKSPACE_SECONDARY_DAEMON_URL` enables transfer tests between two daemons
with separate home and log directories; they may share containerd locally.

## Cached image storage measurements

Export `docker.io/library/alpine:3.22` with `ctr images export --platform linux/amd64`,
then create a reproducible layered fixture:

```sh
python3 workspace/platform/container/tests/make-image.py /tmp/alpine.tar /tmp/storage-2g.tar
sudo "$(command -v ctr)" --address /run/pwn.college/containerd/containerd.sock --namespace k8s.io \
  images import --snapshotter erofs --platform linux/amd64 /tmp/storage-2g.tar
python3 workspace/platform/container/tests/benchmark.py --output /tmp/erofs.json
```

The fixture has four added layers totaling 2 GiB, half random data and half zeros.
The harness verifies whiteouts, overrides, private writes, and full payload hashes.
`make-image.py --gib 20` produces a highly compressible 20 GiB capacity fixture.
Its compression ratio is not representative of real images.

## Startup bursts

```sh
python3 workspace/platform/container/tests/burst.py \
  --count 100 --arrival-seconds 10 --output /tmp/erofs-arrivals.json
python3 workspace/platform/container/tests/burst.py \
  --count 100 --arrival-seconds 0 --output /tmp/erofs-simultaneous.json
```

All images must already be pulled. Each request gets a new 1 GiB home, and all
VMs stay alive until the last start completes. The harness records every request,
latency, failure, and host memory/CPU sample, then stops its workspaces and deletes
its homes. It skips new starts below 16 GiB of available host memory by default.
This guard is for local measurement; it is not production admission control.
Use `--image 'registry/repository:{i}'` to exercise distinct prepared images.
The harness records start response latency separately from successful command
execution, which waits for initialization. Use `--init-read-mib 256` with the
synthetic fixture to read and hash 256 MiB during each workspace initialization.
Measurements exclude Cloudflare latency and remote home downloads. Avoid
concurrent builds during performance measurements.

CRI pulls use `discard_unpacked_layers`; `ctr images import` does not exercise
that behavior. To validate GC, pull unique registry images through
`POST /api/container_images/pull`, check their original layer digests have left
the content store, and start them after GC. Shared layer ancestry should produce
one set of base EROFS files plus the distinct top layers.
