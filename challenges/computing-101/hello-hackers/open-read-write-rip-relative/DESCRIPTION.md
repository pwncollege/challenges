In the previous level, you built the filename on the stack one byte at a time.
That works, but assembly can also store fixed bytes directly in your program.

Assembly source can contain data as well as instructions.
Linux expects filenames to end with a zero byte.
The `.asciz` directive writes a string's bytes and automatically adds that zero byte.

```asm
path:
    .asciz "/flag"
```

The label `path` names the address where those bytes begin.
The `open` syscall needs that address in `rdi`.

On 64-bit x86, you cannot copy the instruction pointer directly with an instruction like `mov rdi, rip`.
The instruction pointer is special: the CPU uses it to know where it is executing.
It is not exposed as a normal source register.
x86-64 does, however, support memory addresses written relative to `rip`.
The `lea` instruction lets you calculate one of those addresses without reading from it:

```asm
lea rdi, [rip + path]
```

This puts the address of `path` into `rdi`.
It does not load the bytes at `path`; that would be `mov rdi, [rip + path]`, which is not what `open` wants.

Because your program now has both instructions and data, write it as a real assembly file:
Put the string after your final `exit` syscall, where your program will never execute it:

```asm
.intel_syntax noprefix
.global _start

_start:
    # your syscalls here
    mov rax, 60
    mov rdi, 42
    syscall

path:
    .asciz "/flag"
```

**Your turn!**
This time, no arguments are passed to your program.
Store the filename with `.asciz`, load its address with `lea rdi, [rip + path]`, and use it to open the flag.

Your program should:

1. Store `"/flag"` as a null-terminated static string with `.asciz`.
2. Load the address of that string into `rdi` with `lea`.
3. `open` it (syscall `2`): `rsi` = `0`.
4. `read` from the returned fd into memory (syscall `0`).
5. `write` the bytes to stdout (syscall `1`).
6. `exit` with code `42` (syscall `60`).

Assemble and link your program, then pass the executable to the checker:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -o solve solve.o
hacker@dojo:~$ /challenge/check ./solve
```

----
**DEBUGGING:**
Having trouble?
Use `strace` to trace your syscalls.
If `open` returns `-1`, your string pointer might be off.
Try `x/s &path` in `gdb` to see the string stored in your program.
