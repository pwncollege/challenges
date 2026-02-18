# Assembly Crash Course Coverage Gap Report

## Summary of findings
- Scope reviewed:
  - `assembly-crash-course`: all 30 listed challenges (`level-1` through `level-23`, including split variants like `-a`/`-b`), `module.yml`, top-level `DESCRIPTION.md`, and all `challenge/run.j2` source.
  - Other `computing-101` modules (excluding `common`): `assembly-assortment`, `building-a-web-server`, `control-flow`, `debugging-refresher`, `hello-hackers`, `introspecting`, `memory`, `the-stack`, `your-first-program`.
  - Readable level configs and source used where present (`module.yml`, `dojo.yml`, `challenge.yml`, `.init`, `chal.py`, `chalconf.py`, `run.j2`, etc.).
- High-level result:
  - `assembly-crash-course` is the only module that covers the full arc from arithmetic/data movement through memory sizing, stack mechanics, jump taxonomy, loops, and function stack frames in one progression.
  - Some fundamentals are strongly duplicated elsewhere (register moves, basic memory dereference, stack basics, cmp/jumps, jump tables, syscall usage).
  - Several advanced assembly topics are effectively unique to `assembly-crash-course` (especially division/modulo internals, subregister tricks, fixed-distance relative-jump padding, and function-frame construction with stack-local data structures).

## Concept coverage matrix

| Assembly-crash-course concept | Crash-course levels | Also covered in other computing-101 modules | Coverage status |
|---|---|---|---|
| Register initialization with `mov` | 1, 2-a | `your-first-program` (`rax`, `movreg`), `hello-hackers` (syscall register setup) | Well-covered elsewhere |
| Multi-register state setup (including non-argument regs) | 2-a | `your-first-program` (multiple register use), `debugging-refresher` (register inspection/modification) | Partial elsewhere |
| Basic arithmetic with `add` | 2 | `assembly-assortment/add-reverse` | Well-covered elsewhere |
| Signed multiplication (`imul`) in expressions | 3 | No direct equivalent module exercise | Unique to assembly-crash-course |
| Integer division mechanics (`rdx:rax`, quotient in `rax`) | 4 | No direct equivalent module exercise | Unique to assembly-crash-course |
| Modulo via `div` remainder behavior | 5 | No direct equivalent module exercise | Unique to assembly-crash-course |
| Subregister byte access (`ah` / upper byte of `ax`) | 6-a | No direct equivalent module exercise | Unique to assembly-crash-course |
| Fast modulo via power-of-two / low-byte register trick | 6 | No direct equivalent module exercise | Unique to assembly-crash-course |
| Bit shifting (`shl`/`shr`) for byte extraction | 7 | No direct equivalent module exercise | Unique to assembly-crash-course |
| Bitwise logic (`and`/`or`/`xor`) as data transform | 8, 9 | `assembly-assortment/xor-reverse` (XOR-focused only) | Partial elsewhere |
| Branchless parity/even check via bit-logic constraints | 9 | No direct equivalent module exercise | Unique to assembly-crash-course |
| Absolute memory read from known address | 10-a | `memory` (`mem-load`, dereference sequence) | Well-covered elsewhere |
| Memory write to known location | 10-b | `hello-hackers/open-read-write-hardcode` (byte stores to memory), reverse binaries in `assembly-assortment`/`control-flow` write bytes | Partial elsewhere |
| Read-modify-write memory update | 10 | No direct equivalent module exercise | Unique to assembly-crash-course |
| Sized memory loads (`byte/word/dword/qword`) | 11-a, 11 | Other modules mainly use `BYTE PTR` only; no full-width comparison exercise | Unique to assembly-crash-course |
| Little-endian representation and large immediate memory writes | 12 | Implied in other modules, but not taught as explicit objective | Unique to assembly-crash-course |
| Pointer + offset arithmetic over adjacent words | 13 | `memory/mem-offsets`, `the-stack/mem-stack-offsets` | Well-covered elsewhere |
| Stack LIFO operations (`push`/`pop`) | 14, 15 | `the-stack/mem-pop`, `introspecting/gdb-pop` | Well-covered elsewhere |
| Stack-pointer direct addressing (`[rsp+off]`) for computation | 16 | `the-stack` module (`mem-stack`, `mem-stack-offsets`, `mem-argv1`) | Well-covered elsewhere |
| Absolute jump control-flow (`jmp reg` to address) | 17-a | `control-flow` (unconditional/conditional jump usage generally) | Partial elsewhere |
| Relative jump targeting with exact byte distance (`nop`, labels, `.rept`) | 17-b | No direct equivalent module exercise | Unique to assembly-crash-course |
| Jump trampoline composition (relative + absolute + stack transfer) | 17 | No direct equivalent module exercise | Unique to assembly-crash-course |
| Conditional branching with multi-case arithmetic paths | 18 | `control-flow` (`cmp-setz`, `cmp-jne`, `cmp-string`) | Well-covered elsewhere |
| Indirect jumps and jump-table dispatch | 19 | `control-flow/switch` | Well-covered elsewhere |
| Counted loop over dynamic-length numeric array (`for`-style) | 20 | `control-flow/loop` (looping concept, string compare) | Partial elsewhere |
| Sentinel-based `while` over bytes (non-zero count, null handling) | 21 | `control-flow/loop`, `assembly-assortment/strcmp-stored` | Well-covered elsewhere |
| Function construction with `call`/`ret`, SysV ABI, external function call | 22 | `debugging-refresher/broken-functions` (analysis of functions, not authoring equivalent logic) | Partial elsewhere |
| Function stack frame design (`rbp`/`rsp`), stack-local table, frame restoration | 23 | No direct equivalent module exercise | Unique to assembly-crash-course |

## Unique to assembly-crash-course
If `assembly-crash-course` were removed, these concepts would have no strong replacement in the rest of `computing-101`:
- Signed multiplication and expression composition (`imul`) as a primary task.
- Division/modulo internals with `rdx:rax` semantics.
- Subregister granularity tricks (`ah`) and power-of-two modulo optimization via register-width selection.
- Shift-based extraction workflows (`shl`/`shr`) as a central objective.
- Full memory-width access training (`byte`, `word`, `dword`, `qword`) and explicit little-endian write reasoning.
- Relative jump distance engineering using filler (`nop`) and assembler repetition directives.
- Jump trampoline construction as a composed control-flow pattern.
- Authoring nontrivial ABI-compliant functions with explicit stack-frame allocation/restoration and stack-local frequency structures.

## Well-covered elsewhere
These crash-course concepts have strong overlap in other modules:
- Basic register setup and movement (`mov`, register roles).
- Fundamental memory dereference and offset addressing.
- Stack basics (`[rsp]`, `[rsp+offset]`, `pop`, argv pointer layout).
- Core conditional control-flow (`cmp`, `jne`/`je`, labels, fall-through vs branch).
- Jump-table/switch style dispatch.
- Looping over byte/string data until terminator.
- Syscall-oriented register usage patterns (especially in `hello-hackers` and `building-a-web-server`).

## Bottom line
`assembly-crash-course` is not just redundant practice. It is the only `computing-101` module that systematically ties together advanced arithmetic semantics, granular data-width/register tricks, precise jump mechanics, and full function-frame implementation. Removing it would leave clear instruction-level gaps even though foundational topics are duplicated elsewhere.
