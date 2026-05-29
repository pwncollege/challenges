So far, every program you've written has been a complete executable: it starts at `_start`, runs from there, and exits with a syscall.
In this challenge, your code will be **a single function inside a shared library**, not a standalone executable.

A shared library (called a `.so` file on Linux) is a chunk of compiled code that some _other_ program loads at runtime and calls into.
Typically, such libraries perform some utility functions, such as parsing image files (e.g., `libpng` parses PNG files) or handling general system-facing tasks (`libc` provides a lot of memory management, file management, and system interaction code).
Deep inside, the actual interaction with the operating system takes place using system calls, but libraries provide a better interface to interact with than raw system calls.

In this challenge, the grader plays the role of program that loads your library (using `libc`'s `dlopen` functionality, looks up finds your function, and **calls it** with arguments).
Your code is the _callee_; the grader is the _caller_.

This is different than anything you've written so far in several ways:

- You don't write `_start` --- the grader is the one with an entry point.
- You don't exit (`mov rax, 60; syscall`) at the end --- exit only makes sense for a whole program. Your function just hands control back to its caller using the **`ret`** (return) instruction.
- Rather than `_start`, you need to mark your function as a global symbol named `solve` so the grader can find it by name in your library.

**Writing the function.**  
Your assembly should look like this:

```asm
.intel_syntax noprefix
.global solve
solve:
    <your code>
    ret
```

The `.global solve` line tells the assembler "expose this code so other code can find it" --- just like `.global _start` did for executables back in the [building](/computing-101/your-first-program) level.
The `solve:` label actually specifies where the code is.

**Building a shared library.**  
You already know how to assemble a program with `as` and link it with `ld`.
To produce a shared library instead of an executable, pass `-shared` to `ld`:

```console
hacker@dojo:~$ as -o your-solve.o your-solve.s
hacker@dojo:~$ ld -shared -o your-solve.so your-solve.o
```

Then submit the `.so` to the grader:

```console
hacker@dojo:~$ /challenge/check your-solve.so
```

**The calling convention.**  
When the grader calls `solve`, it passes arguments in registers.
In the case of this challenge, your `solve` function must take two arguments:

| Register | Role on entry                                   |
|----------|-------------------------------------------------|
| `rdi`    | First argument (a pointer to a buffer of bytes) |
| `rsi`    | Second argument (the length of that buffer)     |

You've already seen `rdi` used to hold the first argument of a syscall (the exit code, an fd, etc.).
That's because Linux syscalls and Linux functions use the same convention for the first few argument registers.

For this challenge, write the `rsi` bytes starting at `rdi` to file descriptor 1 (stdout) using the `write` syscall (just like before!), then `ret`.
