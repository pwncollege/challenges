The shift instructions slide the bits of a value sideways.
`shl` (**sh**ift **l**eft) moves every bit toward the high end, dropping bits off the top and feeding in zeros at the bottom:

```
  0000 0011   (3)
shl by 2
  0000 1100   (12)
```

Each position you shift left doubles the value, so shifting left by `n` multiplies by 2ⁿ (here, `3 << 2 == 3 * 4 == 12`).
Shifting left is also how you slide a small value up into a higher byte to make room for other values beside it.

The instruction takes the value and a shift amount:

```
shl rax, 4
```

Write a function called `solve` that takes a value in `rdi` and returns it shifted left by 4 bits --- the original value times 16 --- in `rax`.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```
