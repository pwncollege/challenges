# Workspace system

The workspace system consists of a runtime artifact and a trusted node platform.
`runtime/` builds the agent, packages, and user-facing services made available
inside each Kata workspace. `platform/` defines the dedicated containerd CRI
runtime, CNI network, closure-only Nix filesystem view, and workspace daemon.
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

Each workspace runtime generation gets a hardlinked store view below
`<dataDir>/workspace-closures/`. Setup enters a private mount namespace,
unmounts the read-only `/nix/store` bind there, and hardlinks the runtime's
closure into an atomically installed directory. An explicit GC root keeps the
source closure alive. Workspace containers bind the resulting directory at
`/nix/store`, avoiding both exposure of the host's full Nix store and
per-workspace closure setup.
