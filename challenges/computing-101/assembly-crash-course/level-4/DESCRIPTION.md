In this level, you will be working with registers. You will be asked to modify or read from registers.

We will set some values in memory dynamically before each run. On each run, the values will change. This means you will need to perform some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result, which is usually `rax`.

Division in x86 is more special than in normal math. Math here is called integer math, meaning every value is a whole number.

As an example: `10 / 3 = 3` in integer math.

Why?

Because `3.33` is rounded down to an integer.

The relevant instructions for this level are:
- `mov rax, reg1`
- `div reg2`

Note: `div` is a special instruction that can divide a 128-bit dividend by a 64-bit divisor while storing both the quotient and the remainder, using only one register as an operand.

How does this complex `div` instruction work and operate on a 128-bit dividend (which is twice as large as a register)?

For the instruction `div reg`, the following happens:
- `rax = rdx:rax / reg`
- `rdx = remainder`

`rdx:rax` means that `rdx` will be the upper 64-bits of the 128-bit dividend and `rax` will be the lower 64-bits of the 128-bit dividend.

You must be careful about what is in `rdx` and `rax` before you call `div`.

Please compute the following:
- `speed = distance / time`, where:
  - `distance = rdi`
  - `time = rsi`
  - `speed = rax`

Note that distance will be at most a 64-bit value, so `rdx` should be 0 when dividing.
