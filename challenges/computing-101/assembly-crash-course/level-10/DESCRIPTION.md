We will now set some values in memory dynamically before each run. On each run, the values will change. This means you will need to do some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it's `rax`.

In this level, you will be working with memory. This will require you to read or write to things stored linearly in memory. If you are confused, go look at the linear addressing module in 'ike. You may also be asked to dereference things, possibly multiple times, to things we dynamically put in memory for your use.

Please perform the following:

- Place the value stored at `0x404000` into `rax`.
- Increment the value stored at the address `0x404000` by `0x1337`.

Make sure the value in `rax` is the original value stored at `0x404000` and make sure that `[0x404000]` now has the incremented value.
