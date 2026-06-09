Lowercasing set the case bit with `or`.
Uppercasing is the mirror image: you *clear* that same bit.

`and` is the bit-clearing tool --- you used it to mask bits down to zero.
A `0` in the mask forces the result bit off; a `1` lets the original bit through.
So to clear just the `0x20` bit and keep everything else, the mask is `0x20` flipped: `0xDF`.

```
  0110 0001   ('a', 0x61)
& 1101 1111   (0xDF: keep every bit except 0x20)
---------
  0100 0001   ('A', 0x41)
```

```
and rax, 0xDF
```

That clears the case bit of one letter.
This time, though, you'll do it to a whole string.

A string is a run of bytes in memory, one after another, ending in a `0` byte --- the NUL terminator --- that marks where it stops.
To walk it you need a loop: the same `jmp`-back-to-the-top shape you took apart in the [Looping](/computing-101/control-flow/loop) challenge, now written by hand.

So your loop is: look at the next byte; if it's the NUL (`0`), jump past the loop and you're done; otherwise clear its case bit, store the byte back, advance to the next one, and jump back to the top.
The high-level of the loop would be:

```
loop:
  ...
  je done
  ...
  jmp loop
done:
  ...
  ...
  ret
```

Write a function that takes a pointer in `rdi` to a lowercase ASCII string and uppercases it *in place*, looping until the NUL.
It returns nothing.
Call it `str_upper` (it works on a whole string, not one character), and export it with `.global str_upper`.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o str_upper.o str_upper.s
hacker@dojo:~$ ld -shared -o str_upper.so str_upper.o
hacker@dojo:~$ /challenge/check str_upper.so
```
