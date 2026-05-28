So far, every program you've written has been a complete executable: it starts at `_start`, runs from there, and exits with a syscall.
In this challenge, your code will be **a single function inside a shared library**, not a standalone executable.

A shared library (a `.so` file on Linux) is a chunk of compiled code that some *other* program loads at runtime and calls into.
Here, the grader plays the role of that other program: it loads your library with `dlopen`, looks up your function by name, and **calls it** with arguments.
Your code is the *callee*; the grader is the *caller*.

This is a different shape than anything you've written so far:

- You don't write `_start` — the grader is the one with an entry point.
- You don't write `mov rax, 60; syscall` at the end — exit only makes sense for a whole program. Your function just hands control back to its caller using the **`ret` instruction**.
- You need to mark your function as a global symbol named `solve` so the grader can find it by name in your library.

## Writing it

Your assembly should look like this:

```text
.intel_syntax noprefix
.global solve
solve:
    <your code>
    ret
```

The `.global solve` line tells the assembler "expose this symbol so other code can find it."
The `solve:` label gives the symbol a target.

## Building it

You already know how to assemble a program with `as` and link it with `ld`. To produce a shared library instead of an executable, pass `-shared` to `ld`:

```console
hacker@dojo:~$ as -o your-solve.o your-solve.s
hacker@dojo:~$ ld -shared -o your-solve.so your-solve.o
```

Submit the `.so` to the grader:

```console
hacker@dojo:~$ /challenge/check your-solve.so
```

## The contract

When the grader calls `solve`, it passes arguments in registers using the standard Linux x86-64 calling convention:

| Register | Role on entry                    |
|----------|----------------------------------|
| `rdi`    | First argument (a pointer to a buffer of bytes) |
| `rsi`    | Second argument (the length of that buffer)     |

You've seen `rdi` used to hold the first argument of a syscall (the exit code, an fd, etc.).
That's because Linux syscalls and Linux functions use the same convention for the first few argument registers.

For this challenge, write the `rsi` bytes starting at `rdi` to file descriptor 1 (stdout) using the `write` syscall, then `ret`.

The `write` syscall takes:

- `rax`: the syscall number (`1` for `write`)
- `rdi`: the fd to write to
- `rsi`: the pointer to the bytes
- `rdx`: the number of bytes

So you'll need to shuffle your incoming arguments into the right registers before invoking `syscall`.
