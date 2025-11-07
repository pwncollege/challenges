We will now set some values in memory dynamically before each run. On each run, the values will change. This means you will need to do some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it's `rax`.

In this level, you will be working with memory. This will require you to read or write to things stored linearly in memory. If you are confused, go look at the linear addressing module in 'ike. You may also be asked to dereference things, possibly multiple times, to things we dynamically put in memory for your use.

It is worth noting, as you may have noticed, that values are stored in reverse order of how we represent them.

As an example, say:
```
[0x1330] = 0x00000000deadc0de
```

If you examined how it actually looked in memory, you would see:
```
[0x1330] = 0xde
[0x1331] = 0xc0
[0x1332] = 0xad
[0x1333] = 0xde
[0x1334] = 0x00
[0x1335] = 0x00
[0x1336] = 0x00
[0x1337] = 0x00
```

This format of storing things in 'reverse' is intentional in x86, and it's called "Little Endian".

For this challenge, we will give you two addresses created dynamically each run.

The first address will be placed in `rdi`.
The second will be placed in `rsi`.

Using the earlier mentioned info, perform the following:
- Set `[rdi] = 0xdeadbeef00001337`
- Set `[rsi] = 0xc0ffee0000`

Hint: it may require some tricks to assign a big constant to a dereferenced register. Try setting a register to the constant value, then assigning that register to the dereferenced register.
