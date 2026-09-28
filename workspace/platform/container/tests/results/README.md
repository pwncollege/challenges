# Runtime storage measurements

## Layered EROFS with a tmpfs upper

Measured on 2026-09-27 on the same host described below: EPYC 7371,
16 cores / 32 threads, 125 GiB RAM, ext4 on NVMe RAID. Each VM has one
vCPU, 2 GiB RAM, a 1 GiB tmpfs upper, a separate 1 GiB `/tmp`, and a newly
created 1 GiB persistent home. An unrelated VM remained running on the host.
All 100 test VMs stayed alive together before cleanup.

| Scenario | Median | p95 | Maximum |
| --- | ---: | ---: | ---: |
| 100 distinct cached images, arrivals over 10 s | 2.70 s | 2.93 s | 3.11 s |
| Same images, all 100 requests at once | 9.62 s | 9.91 s | 10.03 s |
| Arrivals over 10 s, each initialization reads/hashes 256 MiB | 5.62 s | 6.89 s | 7.36 s |
| Cached Alpine starts over 10 s during a cold image pull | 2.74 s | 2.95 s | 3.01 s |

All four runs had 100 successes, no failures, and no cleanup errors. The first
three rows measure through successful command execution after initialization.
The last row measures the start API response, which waits for agent health but
can precede completion of initialization. Minimum available host memory was
67 GiB for light starts and 40 GiB for the 256 MiB initialization case.
These are local node API measurements with cached images and terminal-only
runtime services. They exclude Cloudflare/WAN latency and remote home downloads.
Host caches were not flushed. They do not establish throughput for arbitrary
challenge initialization, desktop services, or sustained CPU-heavy workloads.

### Sharing and registry blob collection

The 100 distinct images share the same five base layers (Alpine plus four
synthetic payload layers), with one tiny unique sixth layer each. The base has
2 GiB of payload, half zeros and half random data:

- Five shared EROFS files occupy 1,084,911,616 bytes (1.01 GiB).
- All 100 unique top layers together occupy 819,200 bytes (800 KiB).
- All 104 synthetic original layer blobs were absent from the content store
  after CRI pull and automatic GC. Alpine's blob was excluded because other
  existing image references retain it.
- No `rwlayer.img` files exist; writable roots are guest tmpfs mounts.

After stopping the test registry and restarting the normal services, two more
workspaces started from the cached image, checked overrides and private writes,
and read/hashed its full 2 GiB payload with matching hashes.

This verifies sharing for matching layer ancestry. A changed earlier layer
creates a different snapshot chain; identical content at arbitrary positions
is not a promise of global deduplication.

The first local registry pull took 265 s to prepare the synthetic base with
LZ4HC and two compression workers, alongside integration tests and the cached
Alpine burst. The other 99 images reused those layers and each needed only a
tiny top layer. These are local-registry preparation times, not internet pull
estimates. Prepare images before assigning workspaces; the start API already
requires an image to be present. New pulls need temporary space for compressed
registry blobs until unpacking and GC finish.

### Capacity and practical limits

The 2 GiB guest allocation is shared by programs, rootfs tmpfs, `/tmp`, and
kernel caches. Two 1 GiB tmpfs limits do not guarantee that both can be filled.
100 guests at their full 2 GiB allocation require 200 GiB plus host overhead;
the successful light-load burst does not make this 125 GiB host suitable for
that worst case. Heavy file reads also populate private guest caches even when
compressed lower files are shared on the host.

OverlayFS copies a whole lower file into tmpfs on its first data write.
Modifying a large base file can therefore exhaust the 1 GiB upper or guest RAM.
Persistent home writes use their separate ext4 disk. Base image size does not
count toward the tmpfs capacity. Two workspaces each started a 20 GiB base in
2.16–2.17 s with a 1 GiB upper, verified layer overrides and private copy-up,
and read/hashed the entire payload with matching hashes.

The seven integration tests pass, including allocation-limit recovery,
ephemeral data cleanup, persistent home transfer, nested KVM, egress, read-only
Nix storage, overlapping lifetimes, and cleanup after a failed start. All 29
control-plane unit tests also pass. Summary observations: [tmpfs](tmpfs.json).
The repeatable harness and patch rationale are in [the test guide](../README.md).

## Historical devmapper and EROFS comparison

Local run on 2026-09-27, based on commit `cb77974e` plus the uncommitted
storage comparison changes. Both use containerd 2.3.0, Kata Rust 4.2.0,
Firecracker 1.17.0, and the same Linux 6.18.35 guest kernel and Nix runtime.
EROFS uses the additional patches described in [the guide](../README.md).

Host: AMD EPYC 7371, 16 cores / 32 threads, 125 GiB RAM, ext4 on NVMe RAID.
The devmapper development pool uses sparse files and loop devices on that same
host filesystem. This does not measure production devmapper on a dedicated LV.

## Cached image measurements

The same Alpine image plus four synthetic layers contains 2 GiB of payload,
half random data and half zeros. Each backend ran five sequential workspaces
and four concurrent workspaces. Starts include VM boot and waiting for the
workspace HTTP agent. Each workspace then checks layer overrides, whiteouts,
private writes, and hashes every payload file. All 18 hashes match.

| Measurement | Devmapper | Compressed EROFS |
| --- | ---: | ---: |
| Median sequential start | 2.386 s | 2.286 s |
| Four concurrent starts, individual range | 2.417–2.624 s | 2.325–2.365 s |
| Median full 2 GiB read + SHA-256 | 3.288 s | 3.788 s |
| Median first one-byte write + fsync to a 4 MiB base file | 0.774 ms | 10.788 ms |
| Configured root capacity | 32 GiB including image | 8 GiB upper, image separate |

These are small, warm-cache samples with images already prepared locally.
No builds or image imports ran alongside these measurements. Host page caches
were not flushed. They do not establish cold-pull performance, tail latency,
or behavior with hundreds of simultaneous workspaces. Image preparation timings
were collected under other load and are deliberately excluded.

EROFS uses OverlayFS with compressed shared lower layers and an ext4 upper.
Changing an existing lower file causes a file copy-up; devmapper copies changed
blocks. The write measurement includes that distinction and uses a zero-filled
4 MiB file. The read measurement includes hashing and guest Python overhead.

Raw observations: [devmapper](devmapper.json), [EROFS](erofs.json).

## Correctness and capacity

Both backends passed the seven-test control-plane E2E suite, including:

- Start, proxy, replacement, stop, and restart with persistent home data.
- Execution of a nested KVM guest and allowed/denied CNI egress.
- A read-only runtime disk shared across overlapping workspace lifetimes.
- Replacement after a deliberately failed start with disks already attached.
- Home export/import between two local daemons sharing containerd.

Both also started a 20 GiB base image twice and read/hashed its full payload on
each run. The four hashes match. EROFS kept its separate 8 GiB upper filesystem
(7.78 GiB after filesystem metadata), despite the 20 GiB lower image. Devmapper
used a 32 GiB total filesystem (31.20 GiB after filesystem metadata).
The capacity fixture contains zeros; its compression ratio is not representative.

Raw observations: [devmapper capacity](devmapper-capacity.json),
[EROFS capacity](erofs-capacity.json).

The development thin pool was detached and reattached, then devmapper was
selected again. Two more workspaces reused the cached 2 GiB image and produced
the same full-content hash. Its backing files preserve the cached snapshots.

The patched Firecracker package's configured tests passed. The containerd patch
also passed its two focused regression tests for compressed-image fallback and
malformed-image errors. These checks are not the full upstream VMM test suite.

## Assessment

Cached starts are similar in this sample. Devmapper has the simpler integration
and lower first-write cost. EROFS provides compression and separates image size
from writable capacity, but requires patches in Firecracker, the Kata
shim, the guest agent, and containerd. The project selected layered EROFS for
compression and independent writable capacity. These archived measurements
predate the 1 GiB tmpfs upper and separate 1 GiB `/tmp`; the devmapper
implementation has been removed.
