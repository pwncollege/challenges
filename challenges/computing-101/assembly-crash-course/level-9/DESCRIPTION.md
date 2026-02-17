In this level, you will be working with registers. You will be asked to modify or read from registers.

We will set some values in memory dynamically before each run. On each run, the values will change. This means you will need to perform some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it is `rax`.

In this level, you will be working with bit logic and operations. This will involve heavy use of directly interacting with bits stored in a register or memory location. You will also likely need to make use of the logic instructions in x86: `and`, `or`, `xor`.

Using only the following instructions:
- `and`
- `or`
- `xor`

Implement the following logic:

```plaintext
if x is even then
  y = 1
else
  y = 0
```

Where:
- `x = rdi`
- `y = rax`
