In this level, you will be working with registers. You will be asked to modify or read from registers.

We will set some values in memory dynamically before each run. On each run, the values will change. This means you will need to perform a formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it's `rax`.

Modulo in assembly is another interesting concept!

x86 allows you to get the remainder after a `div` operation.

For instance: `10 / 3` results in a remainder of `1`.

The remainder is the same as modulo, which is also called the "mod" operator.

In most programming languages, we refer to mod with the symbol `%`.

Please compute the following: `rdi % rsi`

Place the value in `rax`.
