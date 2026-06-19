In this level, you will be working with registers. You will be asked to modify or read from registers.

We will set some values in memory dynamically before each run. On each run, the values will change. This means you will need to perform some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it's `rax`.

In this level, you will be working with bit logic and operations. This will involve heavy use of directly interacting with bits stored in a register or memory location. You will also likely need to make use of the logic instructions in x86: `and`, `or`, `not`, `xor`.

Shifting bits around in assembly is another interesting concept!

x86 allows you to 'shift' bits around in a register.

Take, for instance, `al`, the lowest 8 (or _least significant_ 8) bits of `rax`.

The value in `al` (in bits) is:

```
al = 10001010
```

If we shift once to the left using the `shl` instruction:

```
shl al, 1
```

The new value is:

```
al = 00010100
```

Everything shifted to the left, and the highest (or _most significant_) bit fell off while a new 0 was added to the right side.

You can use this to do special things to the bits you care about.

Shifting has the nice side effect of doing quick multiplication (by 2) or division (by 2), and can also be used to compute modulo.

Here are the important instructions:

- `shl reg1, reg2` <=> Shift `reg1` left by the amount in `reg2`
- `shr reg1, reg2` <=> Shift `reg1` right by the amount in `reg2`

Note: 'reg2' can be replaced by a constant or memory location.

When we say *significant bit* or *least significant byte*, *significant* means "most important for the value."

- The *least significant bit/byte* carries the smallest weight (the "lowest" place value). For example, when you modify the "lowest" or "rightmost" bit, the value changes just by 1.
- The *most significant bit/byte* carries the highest weight (the "highest" place value).


**For this challenge**, using only the following instructions:

- `mov`, `shr`, `shl`

Please perform the following:
Set `rax` to the 5th least significant byte of `rdi`.

For example:

```
rdi = | B7 | B6 | B5 | B4 | B3 | B2 | B1 | B0 |
Set rax to the value of B4
```
