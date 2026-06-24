So far, every program you've written has been a complete executable: it starts at `_start`, runs from there, and exits with a syscall.
In this challenge, your code will be **a single function inside a shared library**, not a standalone executable.

A shared library (called a `.so` file on Linux) is a chunk of compiled code that some _other_ program loads at runtime and calls into.
Typically, such libraries perform utility functions, such as parsing image files (e.g., `libpng` parses PNG files) or handling general system-facing tasks (`libc` provides a lot of memory management, file management, and system interaction code).
Deep inside, the actual interaction with the operating system takes place using system calls, but libraries provide a better interface to interact with than raw system calls.

This challenge plays the role of a program that loads your library (using `libc`'s `dlopen` functionality), looks up your function by name, and **calls** it with arguments.
In Computer Science nomenclature, your code is the _callee_ and the challenge is the _caller_.

**The `call` instruction.**  
How does the grader get into your code in the first place?
It executes a new instruction you haven't met yet: `call`.

`call <target>` is x86's function-call instruction. It does two things:

1. Pushes the address of the next instruction after the `call` instruction (the _return address_) onto the stack.
2. Jumps to `<target>`.

In our case, the grader runs the equivalent of `call solve`, and execution lands at the top of your `solve` function.
You don't have to do anything special to "receive" the call --- you just start running.

For this first challenge, you also don't have to do anything special to _finish_ the call.
We'll deal with the saved return address in the next challenge; for now, just end your code with the `exit` syscall you already know.
This is the same shape as every program you've written so far --- the only thing that has changed is _who_ started executing you.

**Writing the function.**  
Your assembly should look like this:

```asm
.intel_syntax noprefix
.global solve
solve:
    <your code, ending in an exit syscall>
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
In the case of this challenge, your `solve` function takes two arguments:

| Register | Role on entry                                   |
|----------|-------------------------------------------------|
| `rdi`    | First argument (a pointer to a buffer of bytes) |
| `rsi`    | Second argument (the length of that buffer)     |

You've already seen `rdi` used to hold the first argument of a syscall (the exit code, a file descriptor, etc.).
That's because Linux syscalls and Linux functions use the same convention for the first few argument registers.

For this challenge, the challenge will pass you **your flag** as the buffer, with the flag's length in `rsi`.
Write the `rsi` bytes starting at `rdi` to file descriptor 1 (stdout) using the `write` syscall (just like before!), and then `exit` the process cleanly with code `0`.
Get it right, and your `solve` will print your flag for you!

----
**Hint:** Keep in mind that `write()` takes arguments in the order of: file descriptor (1 in `rdi` for stdout), buffer (pointer to memory, in `rsi`), and size (in `rdx`).
This is _different_ from the arguments your function will be called with, so you'll need to move some stuff around!

**Debugging your solution.**
Since your code is a function inside a shared library, there's no entry point to launch under `gdb` directly --- but you can *give* it one.
Add a tiny `_start` to your code that fakes the grader's call: point `rdi` at a stand-in buffer, set `rsi` to its length, and `call solve`.
Now you can step through your logic in plain `gdb`, with no flag and no privileges needed:

```asm
.global _start
_start:
    push 0x41414141   // put four 'A' bytes (0x41) on the stack to stand in for the flag
    mov rdi, rsp      // first argument: a pointer to those bytes
    mov rsi, 4        // second argument: how many bytes to print
    int3              // optional: gdb breaks here without setting a breakpoint
    call solve        // your solve runs, prints the bytes, and exits on its own
```

Assemble and link it as a normal executable (no `-shared` --- this version has an entry point), then load it in `gdb`:

```console
hacker@dojo:~$ as -o debug.o debug.s
hacker@dojo:~$ ld -o debug debug.o
hacker@dojo:~$ gdb ./debug
(gdb) run
```

Execution stops at your `int3`; step through with the techniques from [Software Introspection](/computing-101/introspecting), watching the registers and the buffer.
If your `solve` is correct, this prints `AAAA` --- and the same logic will print your real flag when you submit the `.so` to the grader.

You can also debug the native harness directly with stand-in bytes instead of the flag.
`/challenge/check` is the Python checker script, so do not load it as the executable in `gdb`.
The native program that loads your `.so` is `/challenge/harness`:

```console
hacker@dojo:~$ gdb --args /challenge/harness your-solve.so
(gdb) run
```

The checker will run that same harness shape with the real flag when you submit your `.so`.
