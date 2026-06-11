---
name: porting-legacy-challenges
description: >-
  Port pwn.college challenges/modules from the legacy / OLD pwnshop engine to this repo's
  modern templated style. Use when migrating a module out of `challenges/legacy/`,
  converting OLD pwnshop `Challenge` classes + Jinja templates into modern
  `challenge/` + `tests_private/` templates, or reproducing a legacy challenge as a
  build-time-compiled SUID template with a deterministic solver. Encodes hard-won
  mechanics: keep the challenge IDENTICAL (only seed-derived variants may differ); the
  seeded-determinism pattern that keeps a challenge body and its solver in lock-step;
  the Jinja/pwnshop gotchas (shebang trimming, include-vs-import context, dynamic
  imports, no trim_blocks); validating the shared "linchpin" templates before fan-out;
  extracting assets from the legacy image; and git-crypt encryption of tests_private.
  Complements the `authoring-challenges` skill (read that too for archetype mechanics).
---

# Porting legacy challenges to the modern style

This is the workflow + the non-obvious mechanics for taking a module that exists only as
the OLD pwnshop engine (or as prebuilt binaries under `challenges/legacy/`) and
re-expressing it as modern, build-time-rendered challenges that pass `pwnshop test`.
Every rule below is here because skipping it cost real rework in a previous port. Also
read the **`authoring-challenges`** skill — it owns the per-archetype mechanics
(Dockerfiles, SUID/exec-suid, `win()`, `common/` templates); this skill owns the
*porting* workflow and the *template-determinism* pattern.

## 0. Orient — find all three sources before writing anything

A legacy port has three inputs. Locate each:

1. **The OLD engine** (the source of truth for *behavior*): pwnshop `Challenge` subclasses
   + their Jinja templates, e.g. `OLD/pwncollege-modules/.../<module>/__init__.py` (classes)
   + `<module>/*.c` / `*.py` (templates) + `OLD/pwnshop/.../templates/base/base.c`. Each
   class sets attributes that drive the template; each class's **`verify()` method is the
   real solve** — it is your test.
2. **The OLD descriptions / dojo** (the source of *learner-facing text*): e.g.
   `OLD/intro-to-cybersecurity-dojo/<module>/<id>/DESCRIPTION.md`, `module.yml` (challenge
   order, names, per-challenge pwnshop class + `attributes`), `.init`, helper scripts.
3. **The legacy validation target** (the *challenge set* to match, and reference solvers):
   `challenges/legacy/.../<module>/` — the auto-imported version (prebuilt binaries +
   `tests_private/test_solve.py`). Enumerate its challenge dirs; that is exactly the set
   you must produce. Its `test_solve.py` files are working (if hacky) reverse-engineering
   solvers you can adapt.

Map every challenge dir to its OLD pwnshop class and `attributes` (from `module.yml`), and
note which are presentation variants of one "level" (e.g. `-python`, `-c`, x86-no-source
share one config). **Placement:** a modern standalone module goes at `challenges/<module>/`
(mirroring how `web-security` was migrated out of `legacy/intro-to-cybersecurity/`), not in
`challenges/legacy/`.

## 1. THE CARDINAL RULE — do not change the challenge

The single biggest mistake is "improving" the challenge while porting. **The binary's
behavior, the file/protocol format, the win conditions, any byte/size budgets, and the
flag-delivery mechanism MUST match the OLD engine exactly.** What may differ: the
*seed-derived per-build details* — magic bytes, version numbers, dimensions, colors,
positions, randomized opcodes. "The same seed may produce a different variant" — that, and
only that, is your freedom. Concretely, in one port these were all *wrong* and had to be
reverted: changing an internal struct representation (a reverser sees a different binary),
simplifying a generated asset, recomputing fixed byte budgets, and swapping a font-rendered
flag for plain text. When in doubt, transcribe the OLD template faithfully (rename
`challenge.X` → your namespace `c.X`, inline the base template's `main`/`win`) rather than
re-deriving. The *solver* in your test is free to use any valid approach; the *challenge*
is not.

## 2. The modern architecture & the determinism pattern (the "template stuff")

Modern challenges are rendered at build time, not shipped as prebuilt binaries. The
linchpin: a challenge's **body** (the rendered binary/script) and its **solver** (the test)
must agree on every seeded value — the body bakes the magic/dims/etc. into the binary; the
test crafts an input that must match. They stay in lock-step because:

> `tools/pwnshop/src/pwnshop/lib/__init__.py` renders **each `.j2` file with a fresh
> `random.Random(CHALLENGE_SEED)`** (constant seed, env `CHALLENGE_SEED`, default 0). So if
> the body and the test run the **same config draws first, in the same order**, they get
> **identical** values.

The pattern that exploits this (and the recommended structure):

- **Per-challenge config is inlined** in the challenge's own `challenge/cimg.c.j2` (and its
  `tests_private/test_solve.py.j2`, and any `generate_flag_image.j2`): a few
  `{% set c.* %}` lines + calls to shared helpers, then `{% include "common/<body>.j2" %}`.
  The config block is **duplicated body↔test on purpose** — the test must rebuild the same
  values. They can't silently drift: same seed + same draws ⇒ same values, and any mismatch
  fails that challenge's own test immediately.
- **Shared algorithms** (image generation, byte-budget computation, the C/py body itself,
  the solve helpers) live in `common/<module>_lib.j2` and `common/<body>.j2`. These are
  genuinely reusable; they are *not* per-challenge config.
- The shared body/test templates **consume a pre-built `c` from include context** — they do
  NOT build it. The leaf builds `c` and `{% include %}`s them.

This mirrors how web-security keeps `flask.py.j2` and `test_exploit.py.j2` in sync via
`generate_names(challenge, random)` called first in both. **Alternative** (only if you
can't re-derive — e.g. an opaque prebuilt asset): the test reverse-engineers the actual
binary (objdump/strings/parse-source), like the legacy universal solvers. It's robust to
any seed but fragile and verbose — prefer seed re-derivation.

See `references/template-recipes.md` for copy-paste minimal leaf/body/test files and the
exact helper-macro shapes (`defaults`, `draw_magic`, namespace mutation, etc.).

## 3. Jinja + pwnshop gotchas (each one bit a real port)

- **No `trim_blocks`/`lstrip_blocks`.** pwnshop passes them as render *variables*, not
  `Environment` options, so they do nothing — `{% if %}` lines leave blank lines. Don't
  fight it for `.c`/`.py`: **clang-format/black reformat the rendered output** (`.c` via
  clang-format, `.py` when `.py` is in the suffixes *or* the first line contains
  `python`). For `.j2` library/config files (imported, not formatted), control whitespace
  with `{%- … -%}`.
- **Shebang must be physical line 1.** Put all `{%- import/set -%}` directives *before* the
  shebang line (each trimmed to emit nothing). If a `{%-` immediately follows the shebang,
  it eats the shebang's trailing newline and merges it into the next content — a Python
  script then has a broken/garbage shebang and `python3` runs *piped stdin as code* (a
  baffling REPL-ish failure). Mirror it: directives first, then `#!`.
- **`{% include %}` passes context; `{% import %}` does NOT.** Compose with
  `{% set var = … %}{% include "…" %}` so the included template sees your vars and the
  `random` global. For `{% import … as lib %}`, pass everything the macro needs as
  arguments (it won't see your context); a macro using the seeded RNG must take `random` as
  a parameter.
- **Relative paths resolve against the importing file**, not the repo root
  (`RelativeEnvironment.join_path` = `normpath(parent.parent / template)`). From
  `<chal>/challenge/x.j2` use `../../common/y.j2`; from `<chal>/tests_private/x.j2` also
  `../../common/y.j2`. An absolute-from-`challenges/` path will be mis-joined.
- **Dynamic import in a macro works and stays deterministic:**
  `{% import "levels/" ~ level ~ ".j2" as lvl %}{{ lvl.configure(c, random) }}` — but a
  template that is *both* rendered (emits output) and *imported* will double-execute its
  top-level draws on import (desync). Keep importable config in macros only.
- **Namespace mutation propagates through macros** (the `generate_names(ns, random)`
  idiom): a macro that does `{% set ns.attr = … %}` mutates the caller's `namespace()`.
  This is how one `setup`/`configure` call configures both body and test.
- **List element assignment** has no syntax — use `{% set _ = lst.__setitem__(i, v) %}`.
  Call a side-effecting macro for its mutation via `{% set _ = lib.helper(c, random) %}`.
- **No `ord`/`bytes.fromhex` filters.** Precompute an ord-map dict in the macro, or do the
  arithmetic (`48 + n // 100` for an ASCII digit). Emit bytes as a C array
  `{ {{ ints|join(', ') }} }` (bulletproof, identical compiled output) rather than a C
  string literal (escaping `\`, `"`, `\x1b`+digit is a minefield).

## 4. Build the linchpin first, then fan out

The shared `common/` templates are a tight coupling: if they're wrong, all N challenges
fail. Author them, then **validate ONE challenge end-to-end with real Docker before
generating the rest** — this proves the include-composition, the seed determinism, the
compile+SUID pipeline, and the test harness at once. Extend the C/py body family-by-family,
re-validating as you add each feature (framebuffer, directives, sprites, …) — debugging a
500-line Jinja-C template only at the simplest level is a trap. Generate the many small leaf
dirs with a shell/python loop, not by hand. Subagents can author files but usually cannot
run `pwnshop test` (no dev-shell Docker), so **validation is serial and yours.**

## 5. Tests = ported `verify()` (standalone executables)

- A test file is a **standalone executable** matched by glob `test*/test_*`, run via
  `docker exec --user=1000:1000`. Needs a shebang **and** `chmod +x` (mode is preserved
  from the `.j2`). **Pass = exit 0.** A raised `assert`/exception (Python) or `set -e` +
  failing `grep` (shell) signals failure.
- **The `FLAG` env var is NOT reliably set.** Don't `os.environ["FLAG"]`. The flag is a
  random `pwn.college{…}` written to `/flag` (root 0400). Match it in output:
  `re.search(r"pwn\.college\{[^}\n]+\}", out)` or `grep -oE 'pwn\.college\{[^}]+\}'`.
  Printing the matched flag also marks the challenge "solved" (the harness checks the flag
  string appears in output).
- Port each OLD `verify()` faithfully: it built its input from `self.<attrs>` (the same
  seeded values) and asserted the flag appeared — your test rebuilds them via the shared
  config and does the same. `tests_public/` = a benign functionality smoke test (no flag);
  `tests_private/` = the real solve.
- Watch the multi-presentation refactor trap: if a solver hardcodes its level, its *test
  leaf* may carry no `cimg_level` — a script that keys off `cimg_level` will skip it and
  leave it without a configured `c`. Verify every body **and** test renders with `c`
  defined.

## 6. Extract assets the OLD source doesn't ship

Legacy challenges often depend on things provisioned by the base image, not the module
source (fonts, tools, data files). If `find OLD -iname …` comes up empty, pull it from the
legacy image:
`nix develop -c bash -c 'docker run --rm pwncollege/challenge-legacy:latest <cmd>'` — e.g.
the `figlet -fascii9` font turned out to be `/usr/share/figlet/ascii9.tlf`, shipped by the
apt package **`toilet-fonts`** (md5-verify against the image; prefer depending on the
package over vendoring the file).

## 7. Encrypt `tests_private` (per-module git-crypt key)

Solves ship encrypted, like every other module. After the module passes:
```
git-crypt init -k <module>
printf '**/tests_private/** filter=git-crypt-<module> diff=git-crypt-<module>\n' > challenges/<module>/.gitattributes
git add challenges/<module>/.gitattributes && git add --renormalize challenges/<module>/   # encrypts the blobs
```
Grant the maintainers in `maintainers.yml` (root/connor/yan): import each pubkey from that
file, then `git-crypt add-gpg-user -k <module> --no-commit --trusted <fingerprint> …`, and
`git add .git-crypt/keys/<module>/`. Verify: `git cat-file -p :<a test_solve>` starts with
`\x00GITCRYPT`, the working tree stays plaintext (key unlocked, so `pwnshop test` still
works), `tests_public`/source stay plaintext, and your key's GPG-user set matches an
existing module's exactly.

## 8. Validate — and prove refactors are safe

- `pwnshop test` runs **only inside `nix develop`**:
  `nix develop -c bash -c 'pwnshop test challenges/<module>/<chal> …'`. The wrapper script's
  exit code is not pwnshop's — grep the log for `All tests passed` / `Some tests failed`.
- Confirm **seed-robustness**: re-run the tricky levels with `CHALLENGE_SEED=42` — a
  per-build-random target with a fixed budget can be seed-sensitive.
- When refactoring the shared templates (e.g. relocating config), **prove it's
  behavior-preserving by byte-diffing renders**: `pwnshop render` the new version, `git
  stash` to the old, render again, `diff`. Byte-identical ⇒ same variant ⇒ same binary ⇒
  the (already-green) Docker result is unchanged, no re-run needed for the unchanged paths.
- Commit only when asked; on an unpushed WIP branch, `--amend` obvious fixes into the single
  module commit rather than stacking commits.
