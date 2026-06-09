A bitwise `or` also compares two values bit by bit, but its rule is the opposite of `and`: each output bit is `1` if *either* input bit is `1`.
That makes `or` the tool for *setting* bits --- turning specific bits on while leaving the rest alone.

Wherever the mask has a `1`, the result bit is forced to `1`; wherever it has a `0`, the original bit passes through unchanged:

```
  0100 0001   ('A', 0x41)
| 0010 0000   (turn on bit 5)
---------
  0110 0001   ('a', 0x61)
```

That example is a real trick.
In ASCII, an uppercase letter and its lowercase partner differ only in bit 5 --- the `0x20` bit.
So turning that one bit on with `or` converts any uppercase letter to lowercase:

```
or rax, 0x20
```

Write a function called `solve` that takes an uppercase ASCII letter in `rdi` and returns its lowercase form in `rax`.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```
