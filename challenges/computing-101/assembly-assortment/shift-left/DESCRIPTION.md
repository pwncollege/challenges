Now put the left shift you just studied into code.

Write a function called `solve` that takes a 64-bit value in `rdi`, shifts it left by 4 positions (multiplying it by 16), and returns the result in `rax`.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```
