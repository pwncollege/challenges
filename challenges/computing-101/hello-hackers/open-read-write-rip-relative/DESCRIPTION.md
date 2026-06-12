In the previous level, you created the filename by writing each byte onto the stack.
That is a useful technique, but it is not the only way to keep a fixed string in an assembly program.

Your assembly can also contain bytes that are not meant to execute.
If you put those bytes after your final `exit` syscall, the CPU will stop before it reaches them.
The bytes will still live in your program's memory.

For strings, the assembler gives you a convenient directive:

```asm
path:
    .asciz "/flag"
```

The `.asciz` directive emits the bytes of the string.
Then it emits the terminating zero byte that Linux expects at the end of a filename.
The `path:` label marks where those bytes start.

That leaves one problem: `open` needs the address of `path` in `rdi`.
On 64-bit x86, the instruction pointer (`rip`) is not a normal register you can copy with something like `mov rdi, rip`.
The architecture lets instructions use addresses relative to `rip`.
It does not give you a direct "put the current `rip` into this register" instruction.

This is where `lea` is useful.
You have used memory operands to load bytes from memory.
The `lea` instruction uses the same address syntax.
It stores the calculated address instead of reading from that address.
For this level, use this form:

```asm
lea rdi, [rip + path]
```

This puts the address of the string into `rdi`.
It does not load the contents of the string into `rdi`.

Put the string after your code, after the final `exit` syscall:

```asm
.intel_syntax noprefix
.global _start

_start:
    # open/read/write/exit here

path:
    .asciz "/flag"
```

Your program should do the same `open`, `read`, `write`, and `exit` sequence as before, with two changes:

1. Store the filename with `.asciz` after your code.
2. Load the filename address for `open` with `lea rdi, [rip + path]`.

Run `/challenge/check` with your program, read the flag, and write it to stdout.
