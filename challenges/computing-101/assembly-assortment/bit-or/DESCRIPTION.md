A bitwise `or` also compares two values bit by bit, but its rule is the opposite of `and`: each output bit is `1` if *either* input bit is `1`.
That makes `or` the tool for *setting* bits --- turning specific bits on while leaving the rest alone.

Wherever the mask has a `1`, the result bit is forced to `1`; wherever it has a `0`, the original bit passes through unchanged:

```
  0100 0001   ('A', 0x41)
| 0010 0000   (turn on 0x20)
---------
  0110 0001   ('a', 0x61)
```

That example is a real trick.
In ASCII, an uppercase letter and its lowercase partner differ only in the `0x20` case bit (zero-indexed bit 5, the sixth bit from the right).
The lowercase value is the uppercase value with the case bit set:

| Uppercase    | Lowercase    |
|--------------|--------------|
| `A` = `0x41` | `a` = `0x61` |
| `H` = `0x48` | `h` = `0x68` |
| `P` = `0x50` | `p` = `0x70` |
| `Z` = `0x5A` | `z` = `0x7A` |

`or` takes its operands the same way `and` does --- the value to modify, then the mask.
Set the case bit with `or`, and any uppercase letter becomes its lowercase form.

Write a function that takes an uppercase ASCII letter in `rdi` and returns its lowercase form in `rax`.
Call it `chr_lower` --- name your functions for what they do, and your code stays readable as it grows.
Export it with `.global chr_lower`.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o chr_lower.o chr_lower.s
hacker@dojo:~$ ld -shared -o chr_lower.so chr_lower.o
hacker@dojo:~$ /challenge/check chr_lower.so
```
