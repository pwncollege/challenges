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
./pwnshop list
./pwnshop test web-security/path-traversal-1
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

## Known Production Parity Constraints

`pwnshop run` and `pwnshop test` use the local challenge runtime to approximate production, but privileged container behavior can still differ from deployed challenges.
Treat production as the source of truth for kernel-global state and host-provided networking features.

Production exposes `/proc/sys` read-only to challenge containers.
Do not rely on a local privileged run that can write `/proc/sys`, and do not let `.init` scripts ignore a failed `sysctl -w`.
Use `set -euo pipefail` in bash `.init` scripts, or `set -eu` in POSIX `sh`, and add an explicit post-check when the setting matters:

```bash
sysctl -w net.ipv4.ip_forward=1
test "$(cat /proc/sys/net/ipv4/ip_forward)" = 1
```

The shared Ubuntu challenge base in `challenges/common/Dockerfile.j2` installs only the default Python/web packages unless a challenge adds more packages.
It does not provide `iptables`, `iptables-legacy`, or `nft` by default.
If a challenge needs firewall rules, add the needed package in the challenge Dockerfile and prefer `iptables-legacy` over `nft`, since production does not provide nftables.
Check the exact binary in the built challenge:

```bash
./pwnshop run --user 0 challenges/MODULE/CHALLENGE /bin/sh -lc 'command -v iptables-legacy && ! command -v nft'
```

Failed `/challenge/.init` output is surfaced by `pwnshop`, so a minimal smoke check for init diagnostics is:

```bash
tmp="$(mktemp -d challenges/.runtime-smoke.XXXXXX)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/challenge"
cat > "$tmp/challenge/Dockerfile.j2" <<'EOF'
FROM ubuntu:24.04
COPY . /challenge
EOF
cat > "$tmp/challenge/.init" <<'EOF'
#!/bin/sh
echo "visible init failure" >&2
exit 42
EOF
chmod +x "$tmp/challenge/.init"
./pwnshop run "$tmp" /bin/true
```

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
systemctl status pwn-challenge-runtime.service
journalctl -u pwn-challenge-runtime.service -b --no-pager
```

## Non-Nix Setup (Not Recommended)

You can run `pwnshop` without Nix, but you must supply:

- `uv` (the `./pwnshop` wrapper uses `uv run`)
- a working Docker environment (daemon + client)

Private tests/solutions are encrypted with `git-crypt`; you will need access to the relevant module key(s) to unlock them.
