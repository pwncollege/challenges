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

## DESCRIPTION.md house style

- Three possible levels: dojo intro (`<module>/DESCRIPTION.md`), sub-module intro, and
  per-challenge (`<challenge>/DESCRIPTION.md`, or the `description:` field in module.yml).
- **Voice scales with difficulty.** Beginner (computing-101, linux-luminarium): warm,
  explains everything, "In this challenge, …", shows console examples, ASCII diagrams,
  at most a single `NOTE:`/`---` separator. Advanced (legacy exploitation): terse, often
  a single imperative sentence ("Overwrite a return address to trigger a win function!").
- **Always read the immediate siblings and match their length, cadence, and formatting.**
  Direct address ("you"), real console blocks, no sermons. Don't spoil the solution —
  describe the goal and the concept.
