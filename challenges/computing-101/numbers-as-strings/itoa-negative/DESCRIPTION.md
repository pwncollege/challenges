Your `itoa` handles non-negative numbers.
But a sum can be negative (your `atoi` reads negative numbers, after all), and a negative number is written with a leading `-`.

The trick is to peel the sign off first, then let the work you already did handle the rest:

- If the input value is negative, write a `'-'`, move your buffer pointer one past it (e.g., `add rsi, 1`), and `neg` the input value to get its magnitude.
- You can `cmp rdi, 0` to compare, and `jl is_negative` (`jl` **j**umps if the previous compared left value was **l**ess than the right one, signed).
- Run your existing digit loop on that (now non-negative) magnitude.
- The total length is the digits you wrote, plus `1` for the sign.

A non-negative number has no sign, so it still prints exactly as before.

Extend `itoa(value, buf)` to handle negative values too.
The calling convention is the same: value argument in `rdi`, buffer argument in `rsi`, total length returned in `rax`.
Remember to `.global itoa`.

Build and submit as before:

```console
hacker@dojo:~$ as -o your-solve.o your-solve.s
hacker@dojo:~$ ld -shared -o your-solve.so your-solve.o
hacker@dojo:~$ /challenge/check your-solve.so
```

Handle the sign, return the length, and score!
