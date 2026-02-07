# Development Environment

This repository ships a Nix flake (`flake.nix`) that provides a working dev environment via `nix develop`.

## Requirements

The flake dev shell currently targets:

- OS/arch: Linux (`x86_64-linux` only)
- Init system: `systemd` (the runtime uses `systemctl` to manage a dedicated Docker daemon)
- Privileges: `sudo` access (used to create and manage `/var/lib/pwn.college/docker` and `/run/pwn.college/docker`)
- Tooling: Nix with flakes enabled (so `nix develop` works)
  - Set `experimental-features = nix-command flakes` in your Nix config.
  - Common locations: `~/.config/nix/nix.conf` or `/etc/nix/nix.conf`.

Notes:

- The dev shell brings its own `dockerd` and config; you do not need to use your host Docker daemon.
- The runtime uses a Unix socket at `/run/pwn.college/docker/docker.sock` and sets `DOCKER_HOST` to point at it.

## Quickstart (Nix)

From the repo root:

```bash
nix develop
```

If flakes are not enabled on your system, add this to `~/.config/nix/nix.conf`:

```conf
experimental-features = nix-command flakes
```

On shell entry, the dev shell will run `sudo pwn-challenge-runtime` to ensure the runtime `dockerd` is reachable and will export `DOCKER_HOST` accordingly.

Then use `pwnshop` for all workflows:

```bash
./pwnshop list
./pwnshop test web-security/path-traversal-1
```

## Troubleshooting

`nix develop` prompts for sudo every time:

- That is expected: the dev shell runs `sudo pwn-challenge-runtime` in `shellHook`.
- If you want fewer prompts, make sure your sudo timestamp is valid (e.g., run `sudo -v` once in another terminal).

`systemctl` errors / "System has not been booted with systemd":

- The runtime is implemented as systemd units and requires a systemd-based host (or WSL with systemd enabled).
- This will not work inside a container that does not run systemd as PID 1.

`Error: dockerd not reachable at unix:///run/pwn.college/docker/docker.sock`:

- Verify you are on a systemd host and have sudo rights.
- Check unit status/logs:

```bash
systemctl status pwn-challenge-runtime.service
journalctl -u pwn-challenge-runtime.service -b --no-pager
```

## Non-Nix Setup (Not Recommended)

You can run `pwnshop` without Nix, but you must supply:

- `uv` (the `./pwnshop` wrapper uses `uv run`)
- a working Docker environment (daemon + client)

Private tests/solutions are encrypted with `git-crypt`; you will need access to the relevant module key(s) to unlock them.
