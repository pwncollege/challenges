# Curriculum scaffolding & universal conventions

Applies to **every** module and archetype. This is the skeleton for wiring challenges
into a curriculum and the house conventions that hold repo-wide.

## Curriculum wiring: dojo.yml → module.yml → resources

A **dojo** (e.g. `challenges/computing-101/`) has one `dojo.yml` at its root that names
it and lists its sub-modules **in display order**:

```yaml
name: Computing 101
type: welcome            # "welcome" (intro curriculum) or "public" (supplementary)
id: computing-101
award:
  emoji: "💻"
modules:
- id: your-first-program
- id: memory
- id: the-stack          # order here = order learners see
```

Each **sub-module** (e.g. `computing-101/the-stack/`) has a `module.yml` listing ordered
`resources:` — interleaved lessons and challenges:

```yaml
name: The Stack
resources:
- name: "System Calls"           # a lecture
  type: lecture
  video: vspq0u2tvhU             # YouTube id
  playlist: PL-ymxv0nOtqox...    # optional
  slides: 1vEuZ1PW8Wvm...        # optional Google Slides id
- type: markdown                 # an inline lesson
  name: Optional Resources
  content: |
    Some **markdown** shown between challenges.
- type: challenge                # a challenge entry
  id: mem-stack                  # must match the challenge dir name
  name: "Reading the Stack"
  visibility:                    # optional — hide until a date
    start: "2099-01-01T00:00:00+00:00"
```

- **Ordering** is purely the order of entries (resources + challenges) in `module.yml`,
  and of `modules:` in `dojo.yml`. To insert a level "after X," put its entry after X's.
- **Hiding:** `visibility: { start: "<ISO-8601 with tz offset>" }`. Far-future (2099) =
  indefinitely hidden; a real date = scheduled release (see `advent-of-pwn/2025`). Valid
  on dojo, module, and challenge entries. **Validate edits with `tools/dojo/parse-dojo-yml`**,
  not just a generic YAML parse. When editing one entry among many similar ones, keep the
  edit target tight so you don't touch an adjacent, pre-existing challenge.

## Universal challenge directory layout

```
<module>/<sub-module>/<challenge>/
├── challenge/
│   ├── Dockerfile.j2     # ALWAYS present (usually includes common/Dockerfile.j2)
│   ├── .setup            # optional: build-time (compile, then delete source)
│   ├── .init[.j2]        # optional: container-start time (per-instance files/perms)
│   └── <archetype files> # program.c / .py/chal.py / server.j2 / bin/* / data ...
├── DESCRIPTION.md        # learner-facing narrative (may also live in module.yml)
├── tests_public/         # functionality tests (plaintext)
│   └── test_*.sh|.py
└── tests_private/        # solve/exploit tests (git-crypt encrypted)
    └── test_solve.sh
```

## Dockerfile.j2

Every challenge ships one. Minimal:

```jinja2
{% include "../../../common/Dockerfile.j2" %}
```

The base (`challenges/common/Dockerfile.j2`) is `FROM ubuntu:24.04`, installs python3 +
flask/requests/pwntools, fetches `exec-suid`, `COPY . /challenge`, runs `/challenge/.setup`
if present (then deletes it + the Dockerfile). Override Jinja blocks to customize, e.g.:

```jinja2
{% extends "../../../common/Dockerfile.j2" %}
{% block additional_packages %}gdb strace binutils gcc{% endblock %}
```

A module's own `common/Dockerfile.j2` may extend the top-level one and add SUID fixups
(e.g. computing-101 does `chmod 4755 /challenge/check`, `chmod 4755 /challenge/submit-number`).
Some archetypes set a var before including (program-misuse: `{% set program_name = "cat" %}`).

## .setup (build) vs .init (start)

- **`.setup`** runs once at image build, then is removed. Use it to compile and strip
  source you don't want to ship:
  ```sh
  #!/bin/bash
  set -e
  gcc -static -O2 -o /challenge/program /challenge/program.c
  chmod 4755 /challenge/program        # SUID
  rm /challenge/program.c
  ```
- **`.init`/`.init.j2`** runs at container start (kept). Use it for per-instance state:
  create/reset files with specific owners/perms, init a DB, etc. `.init.j2` can
  `{% extends "../../common/init.j2" %}`.

## Flag & privilege

- Flag is always the file `/flag`. Code reads it (often via a brief privilege bump) and
  emits it **only on a real solve** (see SKILL.md §2 for per-archetype delivery).
- **`exec-suid`** runs interpreted scripts SUID via a precompiled wrapper. Shebang forms:
  - `#!/usr/bin/exec-suid -- /usr/bin/python3 -I` (checker harness)
  - `#!/usr/bin/exec-suid --real -- /bin/bash -p` (bash, keep real uid 0)
  - `#!/usr/bin/exec-suid --real --environ=none -- /bin/bash -p` (drop env too)
  The **SUID bit on the script** (`chmod 4755`) is what tells `exec-suid` to elevate.

## Tests

- `tests_private/test_solve.sh` performs the **actual published solve** and asserts the
  real flag returns, e.g. `... | tee /dev/stderr | grep "pwn.college{"`. Make it
  deterministic (compute, don't guess). Files must be executable.
- `tests_public/` verifies functionality (binary builds/runs, server responds).
- **`tests_private/**` is git-crypt-encrypted per module:** `.gitattributes` carries
  `**/tests_private/** filter=git-crypt-<MODULE> diff=git-crypt-<MODULE>` (distinct key
  namespace per module). Borrow the key from a sibling checkout under
  `~/pwncollege/challenges*/.git/git-crypt/keys/` rather than prompting for a passphrase.
- Always run via `nix develop --command pwnshop test <path>`.

## Writing the DESCRIPTION.md

Learner-facing prose — treat it as carefully as the code. It's a recurring source of
corrections: a shipped **false** claim ("GDB does not pass your shell's environment"),
and "explain *why*, in the same educational philosophy as the others" / "tighten the text
so it flows with the rest of the module."

**Three levels:** dojo intro (`<module>/DESCRIPTION.md`), sub-module intro, and
per-challenge (`<challenge>/DESCRIPTION.md`, or the `description:` field in `module.yml`).

**Per-challenge structure** — the house shape (see `the-stack-revisited/mem-stack-align`,
`mem-envp`, any `control-flow/*`):
1. **Recap** the thread from the previous level in a sentence, so it reads as a *direct
   continuation*, not a standalone ("In the previous levels, you've read `argc`/`argv`/
   `envp` from the stack. But the actual addresses depend on **how the program was
   launched**…").
2. **Introduce the ONE new concept and *why* it's true** — teach the mechanism, not just
   the task. Use an ASCII diagram for memory/stack layout where it helps.
3. **State what the program does / what counts as success** ("Requires `argc == 1`; hands
   you the flag if `(argv[0] & 0xFFFF) == 0x5390`").
4. **Show how to interact, then the win condition** — a fenced ```` ```console ```` block
   with the `hacker@dojo:~$` prompt, ending on the payoff ("Get the alignment right, and
   the challenge gives you the flag!").

**Two sub-shapes for steps 3–4 — don't confuse them:**
- **Code-writing levels** (write asm/a program that the harness grades): a brief task spec
  + numbered *conceptual* steps + a one-line win is the house pattern (see the
  `nibbling-on-numbers` shift/compare/overflow levels). The learner must be told *what* to
  compute, so this stays — but frame it as **requirements and constraints, not a
  register-level recipe**, and never hand over the part that *is* the puzzle. From the
  by-hand rewrite of `control-flow/caller-saved-registers` and `callee-saved-registers`:
  - Refer to operands/registers by their **group** ("save the caller-saved registers",
    "restore the callee-saved registers"), not an enumerated `push rax; push rcx; …`
    sequence in the steps. Name the full register set once, where you *teach* the concept;
    don't repeat it as a copy-paste solution in the task. (Concrete *values* are fine in
    steps — "set them all to `0x1337`" stayed; it's the solution *mechanics* that get
    abstracted.)
  - State success as constraints ("you *must* call `clobber_function` before
    `flag_function`; you *must* preserve your caller-saved registers across the clobber"),
    and stop — don't spell out the `push`/`call`/`pop`/`call` ordering for them.
  - **Never reveal the non-obvious gotcha that is the actual challenge.** The original
    caller-saved DESCRIPTION wrote "push the seven, *and* `rsi`, because the `flag_function`
    pointer is itself caller-saved and will be clobbered too" — that an *argument* register
    is also caller-saved and must be saved is the whole puzzle; the user cut it. Teach the
    rule; let the learner work out which registers it implicates.
- **Interactive read/decode/encode/convert levels** (the program prompts, the learner
  types answers): **do NOT spec the I/O.** No "it shows you several bytes… for a positive
  one give X, for a negative one give *both* readings… miss it and it'll catch you." The
  program prints its prompts, format, and error feedback itself — write the concept, then a
  single hand-off line ("run `/challenge/decode` and get the flag", or just "Now, put this
  to use. Do it, and get the flag!"). This is exactly the paragraph the user deleted from
  `twos-complement{,-short,-dword}` by hand.

**House-style checklist:**
- Direct address ("you"); warm and explanatory in beginner modules, terse in advanced
  ones — **read the immediate siblings first and match their length and cadence.**
- Fenced blocks tagged ```` ```console ````/```` ```asm ````/```` ```text ````; real
  `hacker@dojo:~$` prompts; at most a single `NOTE:` / `---` separator; no sermons.
- **Explain the *why*, not just the *what*** — that's the educational philosophy the
  module is held to.
- **Every technical claim must be verified** (a 3-line test), never asserted from memory,
  and the phenomenon must be *real*, not produced by the challenge's own scaffolding.
- **No spoilers:** describe the goal and the concept, not the exploit steps (those live in
  `tests_private`). Don't hardcode randomized names in prose — refer to them generically.
- **Link canonical concepts; don't overstate them** (from the caller-saved rewrite): for a
  standard, well-named idea (the calling convention, an ABI, an RFC), link the general term
  to a reference (e.g. Wikipedia) and name it plainly for the platform ("the calling
  convention of your architecture — here, 64-bit x86"), rather than dropping a spec acronym
  ("the System V AMD64 ABI") cold. Fold concrete details into the explanation *with their
  reason* ("`rax`, which callees clobber with the return value, …") instead of a bare
  dash-delimited list. And don't present a convention as a hardware law — note it's a
  convention code *can* violate, even if good code doesn't.
- **Format like the house markdown** (distilled from an edit pass that rewrote three
  DESCRIPTIONs into this style):
  - **One sentence per line** (semantic line breaks), not packed multi-sentence
    paragraphs. "Run `/challenge/x`." and "It shows you …" go on separate lines.
  - Keep fenced code-block contents **flush-left** — no leading indentation inside the
    fence.
  - **Worked examples show the whole progression and label every line** — starting form →
    step(s) → result, each with a short label *including the final answer*, e.g.
    `11100011  the byte, in binary` / `1110 0011  split into two nibbles` /
    `e    3     each nibble → a hex digit` / `->  0xe3  the hex!`.
- **Cut meta-commentary and hedging** — no "nothing new here", "that's your first real
  encoding!", "you're not limited to a single byte!". State the task directly; a short
  playful sign-off ("now go earn that flag!") is fine. Go easy on em-dash asides — prefer
  complete sentences (parentheses are fine), and mind subject–verb agreement ("two hex
  digits *are* one byte").
- **Don't re-teach, don't narrate the binary, lean concise** (distilled from "fix" passes
  that cut a 13-line capstone DESCRIPTION to 3, and the by-hand rewrite of
  `twos-complement{,-short,-dword}`):
  - In a later/capstone level, *name* the concepts the learner already practiced instead of
    re-explaining them — "the four interpretations we've studied (unsigned decimal, signed
    decimal, hex, two's-complement binary)", not a fresh bulleted re-listing with ranges.
  - On a **scaling/"wider" sequel, state the delta and the new concrete numbers, don't
    re-derive the rule.** `twos-complement-short`/`-dword` had re-explained "bit N is the
    sign, a negative value is unsigned minus 2ⁿ…"; the user cut that to "you've done this a
    byte at a time, nothing's special about 8 bits — here's the 16-/32-bit max and min
    (with their bit patterns), go." Give the *numbers* for the new width; assume the rule.
  - Don't narrate the program's own mechanics or its failure behavior ("it shows you a
    byte and asks…", "slip on one and it'll tell you…") — the program prints that itself
    when it runs. The DESCRIPTION carries the *concept* and the win condition, not a
    play-by-play of what the binary does.
  - Default short, and shorter the later you are in a module: a capstone DESCRIPTION can be
    two or three sentences. Skip the hype framing ("This is the capstone", "every
    conversion you've learned, all at once").
- **But the level that INTRODUCES a concept earns a full, motivated build-up** — "lean
  concise" is for sequels, not for the first encounter. For `twos-complement` the user
  *expanded* a terse, clever derivation into: foundations (bytes/bits, register width) →
  the naive approach (sign-magnitude) → why it fails (two zeros, the ALU needing two
  arithmetic algorithms) → two's complement as the fix → its human-cost tradeoff — in a
  plain, warm, motivational register, not a literary/Socratic shortcut. Teach the *why* and
  the history when the idea is new; earn the concision only once the learner has the idea.
