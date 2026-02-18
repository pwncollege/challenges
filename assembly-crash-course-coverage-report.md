# Assembly Crash Course Coverage Report (computing-101)

## Scope and method
This report compares `challenges/computing-101/assembly-crash-course` against every other `computing-101` module except `common`:

- `assembly-assortment`
- `building-a-web-server`
- `control-flow`
- `debugging-refresher`
- `hello-hackers`
- `introspecting`
- `memory`
- `the-stack`
- `your-first-program`

Reviewed sources included each module's `DESCRIPTION.md`, `module.yml`, per-challenge `DESCRIPTION.md`, and readable challenge source/config files (`challenge.yml`, `run.j2`, `check.j2`, `builder.j2`, challenge `*.py`/`*.c` templates). Encrypted `test_solve.sh` files were intentionally skipped.

## Summary of findings
- `assembly-crash-course` is the most comprehensive single module for *writing* x86-64 assembly end-to-end (registers, arithmetic, memory, stack, control flow, loops, functions).
- Many foundational topics are also taught elsewhere (register basics, `mov`, syscalls, memory dereference/offsets, stack basics, `cmp`/conditional branching, loops, switch/jump-table ideas).
- The most removal-sensitive content in `assembly-crash-course` is advanced low-level assembly authoring: exact relative-jump construction, trampoline design, division/modulo mechanics (`rdx:rax`), bit-shift/partial-register tricks, and function/ABI/stack-frame implementation.

## Step 1: Assembly Crash Course concept catalog
Concepts explicitly taught across levels (`module.yml` + level descriptions + level `run.j2` checks):

- Register setup and multi-register initialization (`level-1`, `level-2-a`)
- Arithmetic with registers (`add`, `sub`, `imul`) and linear formulas (`level-2`, `level-3`)
- Integer division and remainder semantics (`div`, quotient/remainder behavior) (`level-4`, `level-5`)
- Modulo optimization with power-of-two masking via partial-register moves (`level-6`, `level-6-a`)
- Subregister/partial-register model (`al/ah/ax/eax/rax`) (`level-6-a`)
- Bit shifts and byte extraction (`shl`, `shr`) (`level-7`)
- Bitwise logic (`and`/`or`/`xor`) and boolean logic construction (`level-8`, `level-9`)
- Memory read/write with absolute and register-indirect addressing (`level-10`, `level-10-a`, `level-10-b`)
- Operand-size-aware memory access (byte/word/dword/qword) (`level-11`, `level-11-a`)
- Little-endian interpretation and writing large constants into memory (`level-12`)
- Memory offsets and contiguous-element processing (`level-13`)
- Stack model, LIFO behavior, `push`/`pop`, top-of-stack transforms (`level-14`, `level-15`)
- Direct stack-pointer access and stack-based aggregation (`[rsp+offset]`, averaging) (`level-16`)
- Control-flow primitives: absolute jump, relative jump, labels, `nop`, `.rept` (`level-17-a`, `level-17-b`)
- Jump trampoline composition (relative then absolute jump) (`level-17`)
- Conditional branching with `cmp`/flags and multi-branch arithmetic paths (`level-18`)
- Indirect jumps and jump-table dispatch (`switch` style) (`level-19`)
- Loop construction over dynamic sizes and sentinel termination (`level-20`, `level-21`)
- Function construction with `call`/`ret` and external function invocation (`level-22`)
- Linux amd64 System V calling convention (arg in `rdi`, return in `rax`) (`level-22`)
- Function stack frames (`rbp`), stack allocation/restoration, stack-local counting arrays (`level-23`)

## Step 2: Other module concept catalog (high-level)
- `your-first-program`: register basics (`rax`, `rdi`, `rsi`), `mov`, syscall model (`exit`), passing syscall args in registers, assembling/linking with `as`/`ld`.
- `hello-hackers`: syscall chaining, `write`/`read`/`open`/`exit`, argument pointers from stack (`[rsp+16]`), byte-wise memory writes (`BYTE PTR`) to build strings.
- `memory`: memory dereference (`[addr]`, `[reg]`), pointers, self-dereference, offsets, stored addresses, double dereference.
- `the-stack`: `rsp` as stack base, `[rsp]` and `[rsp+offset]`, argument pointers on stack, `pop` semantics.
- `control-flow`: `cmp`, ZF-driven logic (`setz`, `jne`, `je`), labels/branching, string comparison by byte offsets, looping with backward jumps, switch/jump-table reverse engineering.
- `assembly-assortment`: reverse-engineering instruction effects (`add`, `sub`, `xor`, `cmp`), .rodata discovery, objdump/gdb-aided inversion.
- `introspecting`: disassembly (`objdump`, gdb `disassemble`), stepping (`starti`, `stepi`), register/memory inspection (`print`, `x`), `strace`, `int3` breakpoint behavior.
- `debugging-refresher`: advanced gdb usage (register/memory inspection/modification, breakpoints, scripting, stepping controls), understanding stack/register state during debugging.
- `building-a-web-server`: syscall-heavy assembly application design (`socket`, `bind`, `listen`, `accept`, `read`, `write`, `open`, `fork`), iterative/concurrent control-flow patterns for HTTP servers.

## Step 3: Concept overlap matrix
Legend: "Covered elsewhere" means at least one non-`assembly-crash-course` module teaches or exercises the concept directly.

| Assembly Crash Course concept | Covered elsewhere? | Other modules covering it |
|---|---|---|
| Register basics and `mov` usage | Yes | `your-first-program`, `hello-hackers`, `memory`, `control-flow`, `the-stack` |
| Multi-register setup for tasks | Yes | `your-first-program`, `hello-hackers`, `control-flow` |
| Integer arithmetic (`add`, `sub`) | Yes | `assembly-assortment` |
| Signed multiply (`imul`) in authored solutions | No (explicit) | None clearly explicit outside crash-course |
| `div` mechanics (`rdx:rax`, quotient/remainder) | No (explicit) | None clearly explicit outside crash-course |
| Modulo via `div` and modulo optimization tricks | No (explicit) | None clearly explicit outside crash-course |
| Partial-register mechanics (`al/ah/ax/eax`) as a learning objective | Partial | `control-flow`/`assembly-assortment` use low-byte registers, but not as deeply as crash-course |
| Bit-shifts (`shl`/`shr`) for extraction | No (explicit) | None clearly explicit outside crash-course |
| Bitwise logic construction (`and`/`or`/`xor`) | Yes (partial) | `assembly-assortment` (especially `xor`) |
| Absolute memory read/write (`[addr]`) | Yes | `memory`, `hello-hackers` |
| Register-indirect dereference (`[reg]`) | Yes | `memory`, `the-stack`, `hello-hackers` |
| Multi-level dereference (pointer-to-pointer) | Yes | `memory` |
| Offset addressing (`[base+offset]`) | Yes | `memory`, `the-stack`, `control-flow`, `hello-hackers` |
| Byte/word/dword/qword access sizing as explicit objective | Partial | `hello-hackers`/`control-flow` use `BYTE PTR`; full size ladder is mainly crash-course |
| Little-endian memory representation/writes | No (explicit) | None clearly explicit outside crash-course |
| Stack LIFO operations with `push`/`pop` | Yes | `the-stack` (especially `mem-pop`) |
| Direct `rsp`-offset stack processing | Yes | `the-stack`, `control-flow`, `hello-hackers`, `introspecting` |
| Absolute jump authoring | Partial | `control-flow` covers jumps, but not dedicated absolute-jump authoring challenge |
| Exact relative-jump layout with labels/`nop`/`.rept` | No (explicit) | None |
| Trampoline design (relative jump + payload + absolute jump) | No (explicit) | None |
| Conditional branching with `cmp` and flags | Yes | `control-flow` |
| Indirect jumps and jump-table dispatch | Yes | `control-flow` (`switch`) |
| For/while loop construction over dynamic inputs | Yes | `control-flow` |
| Function authoring with `call`/`ret` as core objective | No (explicit) | None clearly explicit outside crash-course |
| System V AMD64 function calling convention as required ABI contract | No (explicit) | None clearly explicit outside crash-course |
| Function stack frames with `rbp`, local stack allocation/restore | Partial | `debugging-refresher` inspects `rbp`-relative locals, but crash-course is where learners implement frames |

## Concepts unique to Assembly Crash Course (high risk if removed)
These topics appear uniquely or substantially uniquely in `computing-101` as practical assembly authoring objectives:

- Precise relative-jump engineering (`jmp` distance control with labels + `.rept` + `nop`)
- Trampoline construction patterns
- Full `div`/remainder model and modulo-focused arithmetic challenges
- Power-of-two modulo optimization via subregister behavior
- Explicit, deep subregister semantics (`ah`/`al`/`ax`/`eax` interactions)
- Shift-based byte extraction (`shl`/`shr`) as a primary exercise
- Little-endian write reasoning for large constants
- Function implementation requirements with strict System V AMD64 ABI adherence
- Building/restoring full stack frames and using stack-local data structures for nontrivial algorithms

## Concepts well-covered elsewhere
If `assembly-crash-course` were removed, these concepts would still have meaningful coverage in other `computing-101` modules:

- Basic register usage and `mov`
- Syscall-driven program structure (`exit`, `read`, `write`, `open`, and networking syscalls)
- Memory dereference, pointers, offsets, and stack-based argument access
- Basic stack interaction (`rsp`, `pop`, offsets)
- `cmp`-based decisions, flags, branches (`jne`/`je`), loops, and switch/jump-table control flow
- Reverse-engineering common instruction effects (`add`, `sub`, `xor`, `cmp`) with disassembly/debug tooling
- Tooling for assembly introspection/debugging (`objdump`, `gdb`, `strace`, breakpoints)

## Bottom line
`assembly-crash-course` is not redundant. While foundational assembly mechanics overlap with several modules, it is the only module that systematically combines advanced control-flow construction, arithmetic edge semantics, low-level bit/register tricks, and ABI-correct function/stack-frame implementation in authored x86-64 solutions.
