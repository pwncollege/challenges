`or` always sets the case bit (forcing lowercase); `and` always clears it (forcing uppercase).
Neither one *swaps* case: each only pushes a letter one direction.

To flip a bit --- on to off, off to on --- you need `xor`.
Since `xor` sets a bit exactly when its two inputs *differ*, XORing a bit with `1` inverts it, and XORing with `0` leaves it alone.
So XORing a letter with `0x20` flips its case bit either way: uppercase becomes lowercase, and lowercase becomes uppercase.

```
  0110 0001   ('a', 0x61)        0100 0001   ('A', 0x41)
^ 0010 0000   (flip 0x20)      ^ 0010 0000   (flip 0x20)
---------                      ---------
  0100 0001   ('A', 0x41)        0110 0001   ('a', 0x61)
```

That trick works *because every byte here is a letter*.
The `0x20` bit only means "case" for letters; flip it on a space or a digit and you get a different, wrong character.
The strings you're handed are all `A`-`Z` and `a`-`z`, so a blind toggle of every byte is safe --- no need to check.

Walk the string the same way as before --- load a byte, flip its case bit, store it back, advance, and repeat until the NUL.

Write a function that takes a pointer in `rdi` to a mixed-case ASCII string and swaps the case of every letter *in place*, looping until the NUL.
It returns nothing.
Call it `str_swapcase`, and export it with `.global str_swapcase`.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o str_swapcase.o str_swapcase.s
hacker@dojo:~$ ld -shared -o str_swapcase.so str_swapcase.o
hacker@dojo:~$ /challenge/check str_swapcase.so
```
