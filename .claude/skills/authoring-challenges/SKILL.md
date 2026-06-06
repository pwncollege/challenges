---
name: authoring-challenges
description: >-
  Author, review, or revise pwn.college challenges and curriculum in this repo — any
  module, any archetype (templated web/service, interpreted "checker", compiled SUID
  binary, or legacy). Use when creating a new challenge, level, module, or dojo;
  designing a curriculum sequence; writing DESCRIPTION.md / module.yml / dojo.yml;
  authoring challenge code (Jinja2 templates, Python checkers, C/asm, shell); or fixing
  challenge mechanics (flag delivery, SUID/exec-suid, ASLR, victims, visibility).
  Encodes hard-won rules that previously required user correction: one concept per
  level, extend the common templates instead of hand-rolling, deterministic solves with
  the flag granted only on a real solve, verified-only learner-facing claims, minimum
  moving parts, and testing ONLY under `nix develop`.
---

# Authoring pwn.college challenges

Forward-looking rules for creating/revising challenges and curriculum in this repo with
minimal back-and-forth. **The behavioral rules (§1, §4, §5, §6) are universal across
modules; the mechanics (§2, §3) adapt per archetype.** Every rule exists because
skipping it caused a real user correction. Read this fully, then open the reference for
your archetype.

## 0. Orient before you build
- **Identify the archetype first** (see §7) and **extend the module's common templates
  instead of hand-rolling.** The single biggest way to keep a challenge minimal and
  idiomatic is to `{% extends %}`/`{% include %}` the existing `common/` template
  (`flask.py.j2`, `cmdi.py.j2`, `sqli-pw.py.j2`, `common/check`, `secret-value-checker.py`,
  `common/Dockerfile.j2`, …) and set variables in `{% block setup %}` with `super()`.
- **Confirm the target module.** New levels go in the active module the task points at,
  in dojo/module order. Never author in `challenges/legacy/` (it pulls prebuilt binaries
  from external dojos — not where new content goes). If placement is ambiguous, state
  your chosen path in one line and proceed.
- **Read 2–3 sibling levels first** — their `DESCRIPTION.md`, `challenge/`, `module.yml`,
  and tests. The pattern you need almost always already exists.
- **Never declare a mechanism impossible until you've checked how siblings do it.** The
  blessed pattern (a `bin/gdb` exec-suid wrapper, a `submit-number`, a victim script, a
  seccomp allowance in `runtime/`) is in the repo, not a blank slate or the user's head.

## 1. Pedagogy — the most-corrected area (universal)
- **One new concept per level.** Count what a level introduces and compare to its
  neighbors; if it teaches more than one, split the surplus into its own level — don't
  hide the overload in prose. (A level that bundled five concepts as a "capstone" had to
  be torn apart.)
- **Respect sequencing.** Don't introduce advanced topics (e.g. ASLR) early, even as a
  footnote/`NOTE`. They get their own much-later level.
- **The phenomenon you teach must be REAL, not manufactured by your own scaffolding.**
  If the lesson only "works" because of a wrapper you added (e.g. faking a tool's
  behavior with `env -i`), the design is wrong — redesign, don't ship the contrivance.
- **No unverified claims in learner-facing text.** Never assert how a tool behaves
  unless you've tested it. (Shipping the false "GDB does not pass your shell's
  environment" in a DESCRIPTION was a hard correction.) A 3-line empirical check is cheap.
- **When a design feels contrived, stop and offer 2–4 genuinely different designs**
  ranked by honesty/cleanliness — don't keep patching and defending the contrivance.
- **Match the house voice, scaled to the module.** Beginner modules (computing-101,
  linux-luminarium) explain everything warmly; advanced modules are terse. Read siblings
  to calibrate; keep DESCRIPTIONs to the length and cadence of their neighbors — and to
  their *format*: one sentence per line, fenced code flush-left, worked examples that label
  every line, and no meta-commentary ("nothing new here", "your first X"). Lean concise
  (shorter the later you are in a module) — don't re-teach what prior levels covered or
  narrate the program's own mechanics; the binary explains itself when it runs. For the
  per-challenge DESCRIPTION structure (recap → one new concept + *why* → success
  condition → how-to + win) and a writing checklist, see
  `references/curriculum-and-conventions.md` → "Writing the DESCRIPTION.md".
- **Hand the I/O loop to the program; calibrate depth to new-vs-scaling.** Two corrections
  the user made by hand across the `twos-complement{,-short,-dword}` levels:
  - **Don't spec an interactive read/decode/encode/convert program's behavior.** I had
    written "It shows you several bytes… for a positive byte give X, for a negative byte
    give *both* readings… give the unsigned where the signed was asked and it'll catch you."
    The user deleted every such paragraph. The program prints its own prompts, format, and
    error feedback at runtime — the DESCRIPTION teaches the concept and ends on one line
    ("Now, put this to use. Do it, and get the flag!"). This is *not* the same as the
    code-writing levels, where a brief task spec + numbered conceptual steps + a one-line
    win is the kept house pattern — there the learner must know what to compute; here they
    must not be handed the answer key to an interactive drill.
  - **A genuinely new concept gets MORE, not less.** For the first `twos-complement` level
    the user *expanded* my terse-but-clever derivation into a full motivated build-up:
    foundations → the naive approach (sign-magnitude) → why it fails (two zeros, the ALU
    needing dual algorithms) → two's complement as the fix → its tradeoffs, in a plain warm
    register. "Lean concise / cut it to three sentences" applies to *scaling and follow-up*
    levels — for those (`-short`, `-dword`) the user cut my re-derivation of the rule down
    to: state the delta (wider), give the new concrete numbers (bit patterns, unsigned and
    signed max/min for that width), hand off. Don't re-teach the rule on a wider-width
    sequel, and don't shortcut the motivation on the level that introduces the idea.

## 2. Determinism & flag delivery (the rule that got over-generalized — read carefully)
- **The intended solution must be deterministic — it works every time, no guessing.**
  Disable nondeterminism that would break the intended technique (e.g. ASLR off for a
  fixed-address lesson). What the user objected to was a solve whose *target value was
  random* and whose *flag came through a side channel*, not randomness as such.
- **Randomness is legitimate and often desirable** — as long as it's *not a coin-flip in
  the solve path*: seeded build-time secrets (endpoint/parameter/table names via
  `random_names.j2`, admin passwords), and per-instance/per-run secret *values the
  learner discovers through the intended technique* (e.g. `secret_value = random.randint(...)`
  that the checker knows and validates). These prevent memorized/hardcoded solutions.
  Builds are seeded (`CHALLENGE_SEED`) so they're reproducible.
- **Never hardcode or assume the flag's length — it's a variable-length implementation
  detail.** Today's flags are `pwn.college{` + base64(32 bytes) + `}` ≈ 57 bytes, but that
  is *not* a contract and has changed before. Two correct patterns:
  - **Size dynamically from the real flag.** Read `/flag` and use its actual length — e.g.
    `gdb-run-args/.init` bakes `FLAG_LEN=$((${#FLAG}+1))` into the generated asm;
    `callee-write/harness.c` uses `strlen(flag)`. Prefer this whenever the *challenge code*
    (not the learner) emits the flag.
  - **When the learner must write a constant byte count** (they hardcode the `write` length),
    pad the flag to a *fixed capacity comfortably larger than any real flag — ≥ 128 bytes*.
    **Keep that size out of learner-facing text too** — say "the flag", not "the 128-byte
    flag"; let the *runtime* checker/harness report the actual count (e.g. caller-frame's
    harness logs `write N bytes from [rsp+0x40]` straight from its `#define`), so nothing goes
    stale when the capacity changes. Keep the one capacity constant in sync across **every
    coupled non-description file**: `chal.py`, the C harness/`#define`, the hand-written asm
    frame/copy count, and the encrypted `tests_private` solve. A `assert pad_count >= 0,
    "flag too long"` that can fire on a longer flag means the capacity is too small (it
    silently breaks students when flags grow) — raise the capacity, don't ship the assumption.
    (caller-frame/mem-envp shipped a 64-byte cap with only ~7 bytes of slack over current
    flags; both had to be widened to 128 — and the descriptions kept size-agnostic.)
- **Grant the flag only on a real solve, via the archetype's normal mechanism** — don't
  bolt on indirection the design doesn't need:
  - **SUID binary:** open `/flag` pre-drop and print it when the success condition is met.
  - **Interpreted checker:** set `give_flag = True` (the harness prints `/flag`), or have
    the learner's own code emit it (`give_flag = False`).
  - **Web/service:** the app reveals `/flag` on successful exploit (admin login, injection,
    victim exfil).
  - **`submit-number`:** the blessed pattern for "read a value, submit it" levels — use it
    when that *is* the lesson; don't graft it onto a challenge that should hand over the
    flag directly.

## 3. Minimum moving parts & code style (universal)
- **Fewest parts that satisfy the literal spec.** Don't add wrappers, launchers, extra
  binaries, `privileged: true`, or indirection the spec doesn't need. (`bin/gdb` wrappers
  and `submit-number` are fine *when the archetype calls for them* — the error was adding
  one to a challenge that didn't.) If a constraint seems to need extra machinery, surface
  it and ask.
- **Write it review-ready on the first pass** (first-draft code was once ~1.6× too long
  and sent back as "really verbose and weird"). Applies to every language:
  - **C:** `<err.h>` (`err`/`errx`/`warn`), not `perror`+return ladders; factor repeated
    read/write & open-then-`dup2` into helpers; comment the *why*. Don't reimplement what
    the kernel gives you (inherited FDs survive `execve` — no memfd copy of `/flag`).
  - **Python checkers / Jinja / shell:** extend the common base, set a few `{% block setup %}`
    vars, override only what differs; don't paste a whole service when a block override
    suffices. Shell: compact `[ cond ] || { echo msg >&2; exit 1; }` guards.

## 4. Testing & integrity — non-negotiable (universal)
- **Run `pwnshop test` ONLY inside `nix develop`.** Outside it, pwnshop silently falls
  through to the host dockerd (stock seccomp) and `personality`/ASLR challenges fail with
  `personality: Operation not permitted`. That EPERM means **"enter the dev shell," not
  "patch pwnshop/the challenge."** See [[feedback_fix_at_devshell_layer]].
- **`tests_private/test_*.sh` runs the actual solve and confirms the real flag** — build
  the reference solution, run it, and `grep "pwn.college{"`. `tests_public` checks
  functionality. Test files must be executable.
- **Never claim tests pass without running them and reading the output;** qualify a pass
  with its environment. Per the global rule, all tests must pass at all times — there is
  no "preexisting flakiness."
- A challenge that passes only because of an invisible ambient runtime affordance (the
  patched dockerd behind `DOCKER_HOST`) is a latent trap — make the dependency explicit.
- When `pwnshop` flakes under `nix develop` (transient build/network blip), **retry the
  same command** — don't pivot to the host daemon or hand-rolled `docker run` for a green.

## 5. Git & communication (universal)
- **On an unpushed WIP branch, just amend** an obvious fix — no permission menus.
- **State git persistence precisely:** working-tree vs committed vs pushed. Never let
  "Done" imply more durability than exists.
- **Never attribute an uncommitted change to "the user" as fact** — show evidence (mtime,
  `git log`) and say what you actually know. Commit/push only when asked.

## 6. Universal conventions quick-reference
- **Curriculum wiring:** a dojo has one `dojo.yml` (`name`/`type`/`id`/`award`/ordered
  `modules:`); each sub-module has a `module.yml` listing ordered `resources:` —
  `lecture` (video/playlist/slides), `markdown` (content), and `challenge` (id/name/
  optional description/visibility). Order = display order.
- **Hide a not-yet-released challenge** via `visibility: { start: "<ISO-8601 w/ tz>" }` on
  its `module.yml` entry (far-future = hidden). Validate with `tools/dojo/parse-dojo-yml`.
- **Every challenge ships `challenge/Dockerfile.j2`** — usually
  `{% include "…/common/Dockerfile.j2" %}` (override `{% block additional_packages %}`/etc.).
- **`.setup` runs at build time** (compile, then delete source); **`.init`/`.init.j2` runs
  at container start** (per-instance files/perms/services). Flag is always at `/flag`.
- **SUID:** compiled binary → `chmod 4755` in `.setup`; interpreted script → shebang
  `#!/usr/bin/exec-suid -- /usr/bin/python3 -I` (or `--real`/`--environ=none` variants).
- **`tests_private/**` is git-crypt-encrypted** per module (`.gitattributes`:
  `**/tests_private/** filter=git-crypt-<MODULE>`). Borrow the key from a sibling checkout
  under `~/pwncollege/challenges*/.git/git-crypt/keys/` instead of prompting for a GPG
  passphrase.

## 7. Archetypes — pick one, then open its reference
- **Templated web / service** (Flask, sqli, cmdi, path-traversal, xss; victims) →
  `references/service-and-web-challenges.md`
- **Interpreted "checker"** (asm/ELF graded by `common/check` + `chal.py`; memory/pointer
  via `secret-value-checker.py`; `submit-number`) → `references/interpreted-checker-challenges.md`
- **Compiled SUID binary** (deterministic addresses, `personality`+memfd, gdb-under-ptrace
  wrapper, cross-context sentinels) → `references/binary-challenge-recipes.md`
- **Curriculum scaffolding & house style** (dojo.yml/module.yml, resources, visibility,
  Dockerfile/.setup/.init, exec-suid, git-crypt, DESCRIPTION voice) →
  `references/curriculum-and-conventions.md`
- **Legacy** (`challenges/legacy/**`) pulls prebuilt binaries from external dojos via
  `Dockerfile.j2` + a stub `test_legacy.sh.j2`; don't author new content here.

## Recurring failure modes to self-check against
1. Hand-rolled what a common template already provides (didn't `extends`/`include`).
2. Added complexity nobody asked for (extra binary, wrapper, `privileged`, indirection).
3. Made an unverified factual claim in learner text or to the user.
4. Made the solve nondeterministic, or gated the flag behind a guess / needless side channel.
   Or assumed a fixed flag length (hardcoded a byte count / too-small pad capacity) — flags vary.
5. Crammed more than one concept into a level, or mismatched the module's voice.
6. Didn't consult siblings / `runtime/` before building or before giving up.
7. Claimed success (tests, push) without verifying, or attributed a change to the user.
