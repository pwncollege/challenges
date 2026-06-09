`shr` (**sh**ift **r**ight) is the mirror of `shl`: it slides every bit toward the low end, dropping bits off the bottom and feeding in zeros at the top.
Shifting right by `n` divides by 2ⁿ, but its other big use is *positioning* --- bringing a byte that sits higher up in a register down to the bottom, where you can mask it off.

Say you want the *second* byte of a value (bits 8 through 15).
First shift it down to the bottom with `shr`, then keep just those 8 bits with the `and` mask from earlier:

```
  .... 1010 1011  0000 0001   (byte 1 = 0xAB, byte 0 = 0x01)
shr by 8
  .... 0000 0000  1010 1011   (byte 1 is now at the bottom)
and 0xFF
  .... 0000 0000  1010 1011   (just byte 1: 0xAB)
```

Two instructions, one idea: shift the byte you want into place, then mask it.
To get the third byte of a register:

```
shr rax, 16
and rax, 0xFF
```

Write a function called `solve` that takes a value in `rdi` and returns its *second* byte --- bits 8 through 15, as a number from 0 to 255 --- in `rax`.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```
