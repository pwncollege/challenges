Here's a new instruction for your toolkit: `and`.

A bitwise `and` compares two values bit by bit.
Each output bit is `1` only if *both* input bits are `1`; otherwise it's `0`.
Here is the rule for a single pair of bits:

```
0 & 0 = 0
0 & 1 = 0
1 & 0 = 0
1 & 1 = 1
```

`and` applies that rule to every bit position at once:

```
  1011 0111   (your value)
& 0000 0001   (the mask)
---------
  0000 0001   (only the lowest bit survives)
```

Notice the mask above is `1` in only one place: the lowest bit.
Wherever the mask is `0`, the output is forced to `0`, so every bit *except* the lowest is wiped out.
What survives is just the value's lowest bit, all on its own.

That lowest bit is special: it tells you whether the whole number is even or odd.
A number is even exactly when its lowest bit is `0`, and odd exactly when its lowest bit is `1`.
So masking off everything but the low bit --- the way you just did --- hands you the number's parity.

Write a function called `solve` that takes a 64-bit value in `rdi` and returns, in `rax`, `1` if the value is **even** and `0` if it is **odd**.

One thing to watch: the bit you isolate comes out `1` for *odd*, but `solve` has to return `1` for *even*.
So the low bit isn't quite your answer --- it's the answer turned around.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```
