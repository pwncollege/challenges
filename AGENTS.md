# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the pwn.college challenge monorepo containing cybersecurity CTF challenges. Challenges are organized as directories under modules (e.g., `web-security`, etc.) and are built as Docker containers for deployment.

## Authoring Rules (read before creating/reviewing challenges)

Distilled from repeated past corrections. The full, archetype-specific playbook +
copy-paste recipes are in the **`authoring-challenges` skill**
(`.claude/skills/authoring-challenges/`); load it whenever you create, review, or revise a
challenge, level, module, or dojo. Behavioral rules below are universal; mechanics adapt
per archetype (templated web/service, interpreted checker, compiled SUID binary, legacy).

- **Orient first.** Identify the archetype and **extend the module's `common/` templates
  instead of hand-rolling** (flask/cmdi/sqli, `common/check`, `secret-value-checker.py`,
  `Dockerfile.j2`). Put new levels in the active module (not `challenges/legacy/`). Read
  2–3 sibling levels, and check how they solve a problem before declaring it impossible or
  asking for internals.
- **Pedagogy:** one new concept per level (split the surplus into its own level, don't
  hide it in prose); don't introduce advanced topics early; the phenomenon taught must be
  *real*, not manufactured by your own scaffolding; **never put an unverified factual claim
  in learner-facing text** — test it first; match the module's voice *and format* (one
  sentence per line, fenced code flush-left, lean and concise, no meta-commentary like
  "nothing new here", no re-teaching prior levels, and let the program narrate its own
  mechanics rather than the DESCRIPTION).
- **Determinism & flag:** the intended solve must work deterministically (no guessing).
  Seeded build-time / per-instance randomness is fine and good (names, passwords, a secret
  the learner *discovers* via the intended technique) — just not a coin-flip in the solve
  path. Grant the flag only on a real solve, via the archetype's normal mechanism (SUID
  binary prints it; checker `give_flag`; web app reveals on exploit; `submit-number` for
  read-a-value levels). Don't add wrappers/extra binaries/indirection the spec doesn't need.
  **Never assume the flag's length** — it's a variable-length implementation detail (~57
  bytes today, not a contract). Size buffers/byte-counts dynamically from the real `/flag`,
  or pad to a fixed capacity **≥ 128 bytes** kept in sync across every coupled file; an
  `assert "flag too long"` that can fire on a longer flag silently breaks students. Keep the
  size out of learner-facing descriptions too (say "the flag", not "the 128-byte flag"; let
  the runtime checker/harness report the count).
- **Code:** lean, idiomatic, review-ready on the first pass, in every language (extend the
  common base; C: `<err.h>`, helpers, why-comments; don't reimplement what the framework or
  kernel already gives you).
- **Testing integrity:** run `pwnshop test` **only inside `nix develop`** (outside it,
  `personality`/ASLR challenges fail with `personality: Operation not permitted` — that
  EPERM means *enter the dev shell*, not *patch pwnshop/the challenge*). `tests_private`
  runs the real solve and greps the flag. **Never claim tests pass without running them**;
  qualify a pass with its environment.
- **Git/comms:** on an unpushed WIP branch just amend obvious fixes (no permission menus);
  state persistence precisely (working-tree vs committed vs pushed); never assert an
  uncommitted change is "the user's" without evidence.

## Key Commands

### Dev Environment (Nix)

`nix develop` is required for `pwnshop`. Always enter the dev shell before invoking `pwnshop` (or `./pwnshop`) -- if anything fails unexpectedly, your first check should be whether you are inside the dev shell.

```bash
nix develop
pwnshop test challenges/web-security/path-traversal-1
```

The dev shell starts a project-local `dockerd` (see `runtime/`) and exports `DOCKER_HOST` at it. That daemon ships with a patched seccomp profile (`runtime/seccomp.nix`) that allows extra `personality()` values including `ADDR_NO_RANDOMIZE` and `READ_IMPLIES_EXEC` -- challenges that disable ASLR via `personality()` rely on this. Outside the dev shell, `pwnshop` silently falls through to the host `dockerd` with stock moby seccomp, and those challenges fail with `personality: Operation not permitted`. Do not "fix" that EPERM by patching pwnshop; enter `nix develop`.

Requirements for `nix develop`: Linux (`x86_64-linux`), `systemd`, `sudo`, and Nix flakes enabled (`experimental-features = nix-command flakes` in `~/.config/nix/nix.conf` or `/etc/nix/nix.conf`). See `docs/development.md`.

### Challenge CLI

All workflows run through the `pwnshop` CLI (implemented in `tools/pwnshop/src/pwnshop/commands` and backed by shared helpers in `tools/pwnshop/src/pwnshop/lib`).

Each subcommand accepts either a direct path or a challenge slug (e.g., `challenge/web-security/path-traversal-1`). Slugs must contain the base path to all challenges ("challenge"), then the module and challenge.

Primary commands:

```bash
# Test a challenge end-to-end
pwnshop test challenges/MODULE_ID/CHALLENGE_ID

# Example: Test path-traversal-1
pwnshop test challenges/web-security/path-traversal-1

# Render a single template file for debugging
pwnshop render challenges/MODULE_ID/CHALLENGE_ID/path/to/file.j2 --output /tmp/rendered-file

# Build a challenge image without tests
pwnshop build challenges/MODULE_ID/CHALLENGE_ID

# List challenges grouped by key, optionally filtered by git history
pwnshop list --modified-since origin/main

# Drop into an interactive shell (use --user/--volume, or append a command)
pwnshop run --user 0 --volume /tmp/debug challenges/web-security/path-traversal-1 /bin/ls -la /challenge
```

DO NOT run these scripts without pwnshop: the dependencies are not installed in the host, and some of these challenges do permanent damage to their environment.

## Architecture

### Directory Structure
- `challenges/MODULE_ID/CHALLENGE_ID/challenge/`: Challenge source code and artifacts. IF YOU PROVIDE A DOCKERFILE, PUT IT HERE
- `challenges/MODULE_ID/CHALLENGE_ID/tests_public/`: Unencrypted functionality tests
- `challenges/MODULE_ID/CHALLENGE_ID/tests_private/`: Encrypted exploitation tests
- `challenges/MODULE_ID/common/`: Shared Jinja2 templates for the module

### Templating System
- Files ending in `.j2` are Jinja2 templates rendered during build
- Templates receive a `challenge` object with seeded RNG functions
- Template permissions are preserved when rendering (make .j2 files executable if output should be executable)
- Python templates are auto-formatted with Black
- C templates are auto-formatted with astyle

### Template Inheritance and Variables
- Challenge templates should use `{% extends %}` not `{% include %}` when referencing shared templates from `common/`
- Use `{% block setup %}` to set variables on the `settings` namespace
- Call `super()` in setup blocks to preserve parent template initialization
- The `settings` namespace is created by flask.py.j2 and passed through the template hierarchy
- Random values (endpoints, parameters) are generated by `random_names.j2` macro

### Critical Template Details
- Python scripts that need SUID should use shebang: `#!/usr/bin/exec-suid -- /usr/bin/python3 -I`
- Web services (Flask apps) should set `app.config['SERVER_NAME'] = "challenge.localhost:80"` and run on port 80
- Template variables in strings need double braces: `{{variable}}` not `{variable}`
- When using randomization in generated code, use the `random` context variable (e.g., `{{random.randrange()}}`) to evaluate at template time
- Binary challenges may not need templates at all - they can be compiled and placed directly in `challenge/`

### Docker Build Process
1. Every challenge must ship a `Dockerfile.j2` (typically `{% include "common/Dockerfile.j2" %}`) — there is no automatic default.
2. Copies `challenge/` directory to `/challenge` in container
3. Executes `.setup` script if present during build
4. Executes `.init` script if present at container startup

### Testing Framework
- Tests run in temporary containers with a random flag at `/flag`
- Test files must be named `test_*.py` or `test_*.py.j2` and must be executable (`chmod +x`)
- Tests receive `FLAG` environment variable
- Public tests verify functionality
- Private tests contain exploitation logic

## Challenge Development Workflow

1. Create challenge directory: `challenges/MODULE_ID/CHALLENGE_ID/`
2. Create or extend common templates in `challenges/MODULE_ID/common/` if needed
3. Add challenge files to `challenge/` directory (binaries, scripts, configs, etc.)
4. If using templates, extend the appropriate common template and set variables in `{% block setup %}`
5. Make executable files and templates executable: `chmod +x challenges/MODULE_ID/CHALLENGE_ID/**/*.j2`
6. Write `tests_public/test_*.py.j2` for functionality verification
7. Write `tests_private/test_*.py.j2` for exploitation verification
8. Test with: `pwnshop test MODULE_ID/CHALLENGE_ID`

## Example Challenge Template Structures

### Web Challenge (Flask-based)
```jinja2
{%- extends "common/sqli-pw.py.j2" -%}

{% block setup %}
  {{- super() -}}
  {%- set settings.pw_name = "pin" -%}
  {%- set settings.guest_pw = 1337 -%}
  {%- set settings.admin_pw_code = "random.randrange(2**32, 2**63)" -%}
{% endblock %}
```

### Binary Challenge
Can be a C program with or without templating, depending on randomization needs.
Will need to be compiled in an executable .setup file or its custom dockerfile

### Script Challenge  
Can be a simple Python/Bash script with or without templating, depending on randomization needs

## Important Notes

- Docker is required for building and testing challenges
- The `exec-suid` utility is automatically included for SUIDing interpreted programs
- Common Dockerfile lives at `challenges/common/Dockerfile.j2`; include/extend it or provide a custom one as needed.
- Challenge verification should be split between public (functionality) and private (exploitation) tests
- The `challenge` object is available in templates with a seeded `random` attribute for deterministic randomization
- Use existing common templates where possible (flask.py.j2, cmdi.py.j2, sqli-pw.py.j2, etc.)
- Study existing challenges (cmdi-*, path-traversal-*) for patterns and conventions
