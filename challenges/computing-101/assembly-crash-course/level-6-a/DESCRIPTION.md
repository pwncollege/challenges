In this level, you will be working with registers. You will be asked to modify or read from registers.

We will set some values in memory dynamically before each run. On each run, the values will change. This means you will need to do some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result, which is typically in `rax`.

Another cool concept in x86 is the ability to independently access the lower register bytes.

Each register in x86_64 is 64 bits in size, and in the previous levels, we have accessed the full register using `rax`, `rdi`, or `rsi`.

We can also access the lower bytes of each register using different register names.

For example, the lower 32 bits of `rax` can be accessed using `eax`, the lower 16 bits using `ax`, and the lower 8 bits using `al`.

```
MSB                                    LSB
+----------------------------------------+
|                   rax                  |
+--------------------+-------------------+
                     |        eax        |
                     +---------+---------+
                               |   ax    |
                               +----+----+
                               | ah | al |
                               +----+----+
```

Lower register bytes access is applicable to almost all registers.

Using only one move instruction, please set the upper 8 bits of the `ax` register to `0x42`.
