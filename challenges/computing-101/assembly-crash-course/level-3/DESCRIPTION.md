In this level, you will be working with registers. You will be asked to modify or read from registers.

We will now set some values in memory dynamically before each run. On each run, the values will change. This means you will need to do some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it's `rax`.

Using your new knowledge, please compute the following:
- `f(x) = mx + b`, where:
  - `m = rdi`
  - `x = rsi`
  - `b = rdx`

Place the result into `rax`.

Note: There is an important difference between `mul` (unsigned multiply) and `imul` (signed multiply) in terms of which registers are used. Look at the documentation on these instructions to see the difference.

In this case, you will want to use `imul`.
