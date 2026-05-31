# Interpreted "checker" challenges (asm/ELF graded by a Python checker)

One of the four archetypes (see `SKILL.md` §7). This is the dominant pattern in
`computing-101` (assembly-crash-course, control-flow, memory, the-stack). The learner
submits assembly / an ELF / a `.so`; a SUID Python **checker** statically and/or
dynamically validates it and grants the flag. Reuse the shared harness — don't hand-roll.

Read alongside: `computing-101/common/{check,builder,secret-value-checker.py}` and a
sibling's `challenge/{.py/chal.py,check.j2,bin/builder.j2,Dockerfile.j2}` plus its
`tests_private/test_solve.sh`.

## How it fits together

- `challenge/check.j2` → `{% include "../../../common/check" %}` installs the shared
  checker as `/challenge/check` (SUID 4755 via the module Dockerfile). Some sub-modules
  use `run`/`run.j2` (an emulation-based variant) instead.
- `challenge/.py/chal.py` holds the **challenge-specific logic**. The checker does
  `import chal` and calls into it; `chal.py` does `import __main__ as checker` to call
  helpers back.
- `challenge/bin/builder.j2` → the shared `builder` assembles/normalizes the learner's
  input (asm text, ELF, or raw bytes) into a binary + extracts the user's `.text`.

## The checker contract (what `chal.py` defines)

The harness runs up to three stages, each optional — define only what you need:

```python
import __main__ as checker

give_flag = True                 # if True, harness prints /flag when all stages pass
num_instructions = 8             # optional builder constraint (max instrs); allow_asm/allow_elf etc.

# Optional per-stage UX strings (printed around each stage):
check_disassembly_prologue = "Checking your assembly..."
check_disassembly_success  = "Looks right! Running it..."
check_disassembly_failure  = "There's an issue:\n"

def check_raw_binary(raw):       # optional: constrain raw bytes
    ...

def check_disassembly(disas):    # disas = capstone instructions (.mnemonic/.op_str/.operands)
    movs = [d.op_str.split(", ") for d in disas if d.mnemonic == "mov"]
    assert ["rax", "0x3c"] in movs, "Set rax to 60 (0x3c) for the exit syscall!"
    return True                  # raise AssertionError (or checker.ChallengeFailed) to fail

def check_runtime(filename):     # optional: actually run the learner's binary
    rc = checker.dramatic_command(f"{filename}")
    assert rc == 42, f"exit code should be 42, got {rc}"
    return True
```

- **Grant logic:** the harness reads `/flag` with a brief `seteuid(0)` and prints it iff
  `give_flag` is True and no stage raised. Set `give_flag = False` when the learner's own
  code is supposed to print the flag (e.g. `mem-envp`: the flag is placed in the
  environment and the learner's `write` syscall outputs it).
- **Helpers on `checker`:** `read_flag()` (privilege-bumped read of `/flag`),
  `print_prompt()`, `slow_print()`, `dramatic_command()` (run + echo like a shell;
  honors `FAST=1`). Error messages are learner-facing — make them instructive.

## Memory/pointer levels: `secret-value-checker.py`

For "dereference a pointer chain / read a value from memory" levels, don't write a
bespoke checker — include the shared one and configure it:

```jinja2
{# challenge/.py/chal.py.j2 #}
{% include "../../../../common/secret-value-checker.py" %}
```

It builds an assembly prefix that plants a secret in memory, requires the learner to set
specific registers / dereference the chain, and validates the result. The secret is a
per-run `random.randint(...)` — legitimate randomness: the **checker knows it** and the
learner **discovers it through the intended technique**, so the solve stays deterministic.
(Contrast with SKILL.md §2: randomness is bad only when it's a guess in the solve path.)

## `submit-number` levels

For "use a tool to read a value, then submit it" levels (many `introspecting/gdb-*`,
`objdump`, `strace`), the blessed pattern is a SUID `submit-number` program (installed
`chmod 4755`). Use it when *that* is the lesson; don't graft it onto challenges that
should hand over the flag directly.

## DESCRIPTION voice

Conversational, building on the previous level: "So far, your programs have… But real
programs need to **make decisions**…", code in fenced ```asm```/```text``` blocks,
memory layout as ASCII tables, the task as a final imperative. Match the immediate
siblings.

## Test

`tests_private/test_solve.sh` builds a reference solution and greps the flag:

```bash
#!/bin/bash -ex
build() { as -o /tmp/s.o <<< ".intel_syntax noprefix; .global _start; _start: $1" && ld -o /tmp/solve /tmp/s.o; }
build "mov rdi, [rsp]; cmp rdi, 42; setz dil; mov rax, 60; syscall"
/challenge/check /tmp/solve | tee /dev/stderr | grep "pwn.college{"
```

Keep it deterministic; run under `nix develop --command pwnshop test`.
