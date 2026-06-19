In this level, you will be working with registers. You will be asked to modify or read from registers.

We will set some values in memory dynamically before each run. On each run, the values will change. This means you will need to perform some formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it's `rax`.

Many instructions exist in x86 that allow you to perform all the normal math operations on registers and memory.

For shorthand, when we say `A += B`, it really means `A = A + B`.

Here are some useful instructions:
- `add reg1, reg2` <=> `reg1 += reg2`
- `sub reg1, reg2` <=> `reg1 -= reg2`
- `imul reg1, reg2` <=> `reg1 *= reg2`

`div` is more complicated, and we will discuss it later. Note: all `regX` can be replaced by a constant or memory location.

Do the following:
- Add `0x331337` to `rdi`
