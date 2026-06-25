In the previous level, you created the "/flag" filename by writing each byte onto the stack.
That is a useful technique, but it is frustrating to write and hard to reason about (imagine trying to spot a typo in a long sentence written this way!).
This challenge will show you a better way.

Luckily, your assembly can also contain bytes that are not meant to execute.
For example, if you put those bytes after your final `exit` syscall, the CPU will stop before it reaches them.
The bytes will still live in your program's memory, but will not crash your program by being interpreted as instructions.

For strings, the assembler gives you a convenient directive to specify these bytes:

```asm
_start:
    ...
    mov rax, 60
    syscall           // exit!
path:
    .asciz "/flag"    // never executed, but still there!
```

The `.asciz` directive emits the bytes of the string along with the terminating zero byte that Linux expects at the end of a filename.
The `path:` label marks where those bytes start.
In later challenges, when you see a compiled binary load a pointer to a stored string, you are seeing the same idea from the other side: the bytes are stored in the program, and an instruction computes their address at runtime.

That leaves one problem: to pass this path into the `open` syscall, you need to set its address in `rdi`.
In the old days, programs would always be loaded to the same address in memory, and so you could hardcode this, as so:

```asm
_start:
    ...
    mov rdi, path    // this would tell the assembler to store the address of `path` in rdi
    ...
path:
    .asciz "/flag"
```

Unfortunately, **THIS DOES NOT WORK** in cybersecurity contexts!
Modern software is compiled, for security reasons that we will cover in the Yellow belt, to be able to be loaded anywhere in memory.
This means that, at the time of assembly of the software, _the assembler doesn't know the right address_.
While this can be solved at start time for normal applications, modern CPUs have solved this problem in a different way: _Instruction Pointer Relative Addressing_.


On 64-bit x86, the _instruction pointer_ (`rip`) is a register that always contains the address of the _next_ instruction your CPU will execute.
However, it is not a normal register, in the sense that its usage is more limited than something like `rdi` (note that this is a quirk of x86; many other architectures let you directly access their instruction pointer).
That being said, 64-bit x86 _does_ allow you to use addresses relative to `rip` for memory reads and writes.
For example:

```asm
_start:
    ...
    mov rdi, [rip+path]
    ...
path:
    .asciz "/flag"
```

**THIS IS STILL NOT WHAT WE WANT!**
Why? Because it _reads_ the 8 bytes at `[rip+path]` into `rdi` rather than put the address of those bytes into `rdi`.
`rdi` would end up holding the values `'f'`, and `'l'`, and so on, but the `open` syscall needs the address and not the values.
Think of `path` as the address where the first byte of `"/flag\0"` lives: `mov` copies bytes from there, while `lea` copies the address so the kernel can walk those bytes until the null byte.

Luckily, there is an instruction that is _almost_ a read, but instead _does_ put the address that would have been read into `rdi` (or whatever other register).
That instruction is **l**oad **e**ffective **a**ddress (the word _effective_ here refers to the CPU figuring out all the calculations it needs to do, such as adding an offset to the instruction pointer in this case):

```asm
_start:
    ...
    lea rdi, [rip+path]
    ...
path:
    .asciz "/flag"
```

This puts the address of the "/flag" string into `rdi`, rather than loading the contents of the string into `rdi`.

Now, a quick note about the math here: though we write `[rip+path]` above, what _actually_ gets added to `rip` is the delta in addresses between `rip` (which, again, is pointing to the instruction after `lea`) and the "/flag" string.
It's a weird syntax, and yet another little quirk of x86.

Use this in this challenge to set the path passed to `open`.
Your program should open the stored filename, `read` from the returned fd into memory, `write` back exactly the number of bytes `read` returned (`mov rdx, rax`, as in read-exact), and `exit` with code `42`.
The new parts are:

1. Store the filename with `.asciz` after your code.
2. Load the filename address for `open` with `lea rdi, [rip + path]`.

Run `/challenge/check` with your program, read the flag, and write it to stdout!
