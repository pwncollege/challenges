Until now, you've been writing a *loadable library*: a function the challenge loaded and called for you.
This time, you'll write a whole *program* --- one that starts at `_start`, runs on its own, and exits when it's done.

Your program gets the number as a command-line argument.
When a program starts, the stack holds its arguments: `argc` (the count) sits at `[rsp]`, and the argument pointers follow it --- `argv[0]` (the program's own name) at `[rsp + 8]`, and `argv[1]` (the first real argument) at `[rsp + 16]`.
So the number you want is the string pointed to by `[rsp + 16]`.

Read it, convert it with your `atoi`, and hand the value back the way a *program* does: instead of returning it in `rax`, exit with it as your exit code, using the `exit` syscall with the value in `rdi`.
An exit code is a single byte, so the number you're given will be between `0` and `255`.

This time, assemble and link it as a normal program (no `-shared`), then submit it:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ /challenge/check prog
```

Convert the argument and exit with its value.
