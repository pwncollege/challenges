Your `itoa` handles non-negative numbers.
But a sum can be negative (your `atoi` reads negative numbers, after all), and a negative number is written with a leading `-`.

The trick is to peel the sign off first, then let the work you already did handle the rest:

- If the value is negative, write a `'-'`, move your buffer pointer one past it, and `neg` the value to get its magnitude.
- Run your existing digit loop on that (now non-negative) magnitude.
- The total length is the digits you wrote, plus `1` for the sign.

A non-negative number has no sign, so it still prints exactly as before.

Extend `itoa(value, buf)` to handle negative values too: value in `rdi`, buffer in `rsi`, total length returned in `rax`.
Remember to `.global itoa`.

Build and submit as before:

```console
hacker@dojo:~$ as -o your-solve.o your-solve.s
hacker@dojo:~$ ld -shared -o your-solve.so your-solve.o
hacker@dojo:~$ /challenge/check your-solve.so
```

Handle the sign, return the length, and score!
