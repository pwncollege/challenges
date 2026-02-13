In this level, you will be working with registers. You will be asked to modify or read from registers.

We will set some values in memory dynamically before each run. On each run, the values will change. This means you will need to perform some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it's `rax`.

It turns out that using the `div` operator to compute the modulo operation is slow!

We can use a math trick to optimize the modulo operator (`%`). Compilers use this trick a lot.

If we have `x % y`, and `y` is a power of 2, such as `2^n`, the result will be the lower `n` bits of `x`.

Therefore, we can use the lower register byte access to efficiently implement modulo!

Using only the following instruction(s):
- `mov`

Please compute the following:
- `rax = rdi % 256`
- `rbx = rsi % 65536`
