In the previous challenge, your `solve` function received some data and *did* something with it (wrote it out via a syscall).
But your function didn't have to *say anything back* to the grader — it just acted, then returned.

This time, your function has to return a value.

In the Linux x86-64 calling convention, **the return value of a function goes in `rax`**.
You've already seen `rax` used in syscalls — it holds the syscall number on entry and the syscall's result on exit.
The same register, by convention, holds the return value of a regular function.

The mechanics:

1. The grader calls your function, passing one argument in `rdi`.
2. Your function does some work.
3. Your function puts its result in `rax`.
4. Your function executes `ret`, handing control back to the grader.
5. The grader reads `rax` and treats it as your function's return value.

For this challenge:

- `rdi` will contain a secret 64-bit value chosen at random by the grader.
- Your function must return `rdi + 1` in `rax`.

That's it.
The lesson is the calling convention, not the arithmetic.

As before, build a shared library and pass it to the grader:

```console
hacker@dojo:~$ as -o your-solve.o your-solve.s
hacker@dojo:~$ ld -shared -o your-solve.so your-solve.o
hacker@dojo:~$ /challenge/check your-solve.so
```
