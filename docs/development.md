# Development Environment

This repository ships a Nix flake (`flake.nix`) that provides a working dev environment via `nix develop`.

## Requirements

The flake dev shell currently targets:

- OS/arch: Linux (`x86_64-linux` only)
- Init system: `systemd` (the runtime uses `systemctl` to manage a dedicated Docker daemon)
- Privileges: `sudo` access (used to start the challenge runtime)
- Tooling: Nix with flakes enabled (so `nix develop` works; set `experimental-features = nix-command flakes` in `~/.config/nix/nix.conf` or `/etc/nix/nix.conf`)

## Quickstart (Nix)

From the repo root:

```bash
nix develop
```

If flakes are not enabled on your system, add this to `~/.config/nix/nix.conf`:

```conf
experimental-features = nix-command flakes
```

On shell entry, the dev shell will start the challenge runtime (using sudo). This is a dedicated docker daemon, properly configured (see [../runtime/](../runtime) for more details). It also exports `DOCKER_HOST` so Docker and `pwnshop` talk to this daemon.

Then use `pwnshop` for all workflows:

```bash
pwnshop list
pwnshop test web-security/path-traversal-1
```

## Community Dojo Workflow

Add new or ported community dojo content under `challenges/`.
A full dojo uses `challenges/$DOJO_ID/dojo.yml`, module ordering lives in each `module.yml`, and challenge code/tests live under that module's challenge directory.

After changing dojo or module YAML, run `tools/dojo/parse-dojo-yml`.
After changing a challenge, run `pwnshop test` for that challenge from inside `nix develop`.

Private solves in `tests_private/` are encrypted with the git-crypt filter configured by the dojo or module `.gitattributes`.
When adding a dojo that needs encrypted tests or maintainer access, update `maintainers.yml` and check it with `tools/maintainers/check-maintainers`.

Each challenge still builds as its own image from its rendered `/challenge` directory.
Shared Dockerfiles and packages reuse Docker's layer cache, so the monorepo does not require one giant image per dojo.

## Troubleshooting

`nix develop` prompts for sudo every time:

- That is expected: the dev shell starts the challenge runtime via `sudo` in `shellHook`.
- If you want fewer prompts, make sure your sudo timestamp is valid (e.g., run `sudo -v` once in another terminal).

`systemctl` errors / "System has not been booted with systemd":

- The runtime is implemented as systemd units and requires a systemd-based host (or WSL with systemd enabled).
- This will not work inside a container that does not run systemd as PID 1.

`Error: dockerd not reachable at unix:///run/pwn.college/docker/docker.sock`:

- Verify you are on a systemd host and have sudo rights.
- Check unit status/logs:

```bash
systemctl status pwn-platform-runtime-docker.service
journalctl -u pwn-platform-runtime-docker.service -b --no-pager
```

## Non-Nix Setup (Not Recommended)

You can run `pwnshop` without Nix, but you must supply:

- Python dependencies for `tools/pwnshop` (or use `uv run --project tools/pwnshop --with-editable tools/pwnshop pwnshop ...`)
- a working Docker environment (daemon + client)

Private tests/solutions are encrypted with `git-crypt`; you will need access to the relevant module key(s) to unlock them.
