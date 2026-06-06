In the last level you saw two functions fight over `rdi`.
That's a glimpse of a bigger problem: there are only sixteen general-purpose registers, and every function in the program shares them.
When you `call` a function, it's going to use registers for its own work, so what happens to the values *you* had in them?

The answer is determined by the [_Calling Convention_](https://en.wikipedia.org/wiki/Calling_convention) of your architecture (in our case, 64-bit x86), which defines how functions pass arguments and share registers across function calls.
Generally, a calling convention splits registers into two groups so that separately-written functions can cooperate:

- **caller-saved** registers may be freely overwritten by any function you call. If you have a value in one of these that you need *after* a call, it's *your* job (the caller's) to save it first and restore it afterward. Typically, this is done by `push`ing them to the stack before calling the callee and `pop`ing them off the stack later. On x86-64, these registers are `rax` (which callees will clobber by moving the return value to), `rcx`, `rdx`, `rsi`, `rdi`, `r8`, `r9`, `r10`, `r11`.
- **callee-saved** registers must be left untouched by the functions you call. Rather, callees _can_ touch them, but they must restore them back to their original state. On x86-64, these are `rbx`, `rbp`, `r12`, `r13`, `r14`, `r15`.

Note that this convention is just that, a _convention_.
Code can misbehave and violate this, though this doesn't really happen in practice with reasonable code.

This level forces you to explore caller-saved registers.
Your `solve` function is given two arguments:

1. `rdi`: a pointer to a `clobber_function` that will clobber all caller-saved registers
2. `rsi`: a pointer to a `flag_function` that will give you the flag if you call it with your registers un-clobbered

You _must_ call `clobber_function` before `flag_function`.
But you _must_ preserve your caller-saved registers before calling `clobber_function` and restore them afterwards.

Build your shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o your-solve.o your-solve.s
hacker@dojo:~$ ld -shared -o your-solve.so your-solve.o
hacker@dojo:~$ /challenge/check your-solve.so
```

Do it right, and the flag is yours!
