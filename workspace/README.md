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

Containerd's blockfile snapshotter supplies container roots as sparse ext4 disk
images, with an 8 GiB total capacity per container, including the unpacked image
and filesystem metadata. Nix and home disks have their own capacities.
Containerd prepares the empty filesystem once at startup.
Image unpacking uses temporary host loop mounts;
running workspaces attach the image files directly. Nix and home disks also
attach directly, so workspace VMs need no virtiofs daemon or host home mounts.

Two local patches are included: Kata reserves read-only Firecracker
drive slots for immutable images, and containerd uses its existing sparse-copy
helper when preparing blockfile snapshots. Container roots copy allocated data
when created; their empty capacity stays sparse.

The sparse-copy issue is tracked in [containerd PR #12956](https://github.com/containerd/containerd/pull/12956).
Its helper landed in [continuity PR #276](https://github.com/containerd/continuity/pull/276);
our patch connects blockfile to it. Firecracker already supports read-only disks,
but Kata 4.2.0 creates only writable placeholder slots for later attachments.
The Kata patch adds read-only slots and routes immutable disks to them.
