Now use `shr` for positioning.
Move the input's second byte down to the low end, then reuse the mask from [Masking Bits](/computing-101/assembly-assortment/bit-and) to discard everything outside that byte.

Write a function called `solve` that takes a value in `rdi` and returns its *second* byte --- bits 8 through 15, as a number from 0 to 255 --- in `rax`.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```
