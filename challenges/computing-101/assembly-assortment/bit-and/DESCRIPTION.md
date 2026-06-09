You met `and` for the even/odd test; here you'll use it to keep only the bits you want.

A bitwise `and` compares two values bit by bit: each output bit is `1` only if *both* input bits are `1`.
That makes `and` the tool for *masking* --- keeping the bits you want and forcing the rest to zero.

Wherever the mask has a `1`, the original bit passes through; wherever it has a `0`, the result bit is cleared:

```
  1011 0110   (your value)
& 0000 1111   (the mask: keep the low 4 bits)
---------
  0000 0110   (everything above the low 4 bits is gone)
```

In x86 that masking *is* a single `and`, with the mask as the second operand:

```
and rax, 0xF
```

A common use is isolating the lowest byte of a value --- the low 8 bits --- by masking with `0xFF`.

Write a function that takes a 64-bit value in `rdi` and returns, in `rax`, just its lowest byte.
Call it `LOBYTE`, in capitals: standing for **LO**w **BYTE**, and often used as shorthand for this functionality in tools you'll become familiar with later.
Export it with `.global LOBYTE`.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o lobyte.o lobyte.s
hacker@dojo:~$ ld -shared -o lobyte.so lobyte.o
hacker@dojo:~$ /challenge/check lobyte.so
```
