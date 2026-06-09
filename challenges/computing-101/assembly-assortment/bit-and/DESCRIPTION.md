In the last level you reverse-engineered a binary that used `xor`.
Now you'll put the rest of the bitwise family to work yourself, starting with `and`.

A bitwise `and` compares two values bit by bit: each output bit is `1` only if *both* input bits are `1`.
That makes `and` the tool for *masking* --- keeping the bits you want and forcing the rest to zero.

Wherever the mask has a `1`, the original bit passes through; wherever it has a `0`, the result bit is cleared:

```
  1011 0110   (your value)
& 0000 1111   (the mask: keep the low 4 bits)
---------
  0000 0110   (everything above the low 4 bits is gone)
```

A common use is isolating the lowest byte of a value and throwing away everything above it.
The low byte is the low 8 bits, so the mask is `0xFF` (eight `1`s):

```
and rax, 0xFF
```

Write a function called `solve` that takes a 64-bit value in `rdi` and returns, in `rax`, just its lowest byte (the value masked with `0xFF`).

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```
