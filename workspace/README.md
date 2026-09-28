# Workspace system

The workspace system consists of a runtime artifact and a trusted node platform.
`runtime/` builds the agent, packages, and user-facing services made available
inside each Kata workspace. `platform/` defines the dedicated containerd CRI
runtime, CNI network, compressed Nix filesystem image, and workspace daemon.
The platform definition is shared by two activation paths:

- `activate.nix` renders transient units for development on any systemd-based
  Linux host with Nix.
- `module.nix` installs the same definitions through the NixOS module system.

## NixOS

The flake exports `nixosModules.workspace`. A node configuration must
provide the workspace runtime:

```nix
{
  imports = [ inputs.challenges.nixosModules.workspace ];

  services.pwn-workspace = {
    enable = true;
    workspaceRuntime = runtime.runtime;
  };
}
```

An optional `publicKey` enables API request signature verification. It is the
hex encoding of the raw 32-byte Ed25519 public key. The module also supports
overriding the listen address, state paths, workspace subnet, and
optional directory for ext4 home images.

Nix builds each workspace runtime closure into an LZ4HC-compressed EROFS image
in the Nix store. Kata attaches the shared image as a read-only virtual disk and
mounts it at `/nix/store` inside each workspace. The image contains only the
selected runtime's closure. There is no store preparation service or host mount;
the guest reads and decompresses filesystem blocks as needed.

The platform uses Kata Containers 4.2.0's Rust runtime with Firecracker 1.17.0
and its jailer, a matching Kata guest image, and a Linux 6.18.35 guest kernel
that enables KVM and EROFS. Integration tests
execute a nested KVM guest and verify the read-only runtime disk, HTTP/HTTPS
egress, denied egress, workspace lifecycle, and home transfers between nodes.

Containerd stores container images as shared LZ4HC-compressed EROFS layers.
Each workspace gets a separate 1 GiB tmpfs for its writable rootfs.
Kata attaches the layer files through a read-only VMDK descriptor, and guest
OverlayFS combines their contents with the writable tmpfs. Base images can be
larger than 1 GiB; only newly written or copied-up data uses the upper limit.
Updating a file from the image copies the whole file into the upper filesystem, so modifying a sufficiently large image file can exhaust the upper.

The entrypoint mounts a separate 1 GiB tmpfs at `/tmp`, with `nosuid,nodev` and
mode 1777. Its pages consume guest RAM as written; this is a size ceiling, not
reserved or additional memory. The default VM has 2 GiB RAM and one vCPU.
Rootfs writes and `/tmp` share that RAM with programs and the guest kernel; the two limits do not reserve memory
and cannot both be filled alongside programs without exhausting the VM.
Both the rootfs upper and `/tmp` are discarded when the workspace stops.
Persistent home disks have their own capacity and lifecycle.

Ordinary OCI layers are converted during image pull. CRI uses containerd's local
pull path with `discard_unpacked_layers`, allowing GC to remove downloaded layer
blobs after unpacking. The EROFS layers and image metadata remain, shared across
images with the same layer ancestry. Pulls need temporary download space.
The node start API requires an already-pulled image; image conversion is outside
the start request. Native EROFS registry layers are also supported by containerd,
although our current image build pipeline publishes conventional OCI layers.

Nix, image, and home disks attach directly to the VM. Workspaces need no virtiofs
daemon or host home mounts. The platform has one container rootfs implementation:
layered EROFS with a tmpfs upper. Local patches and reproducible storage/load tests
are described in [the runtime test guide](platform/container/tests/README.md).
