One digit was easy.
A two-digit number like `42` needs *splitting* into its tens (`4`) and ones (`2`) --- and splitting is division: `42 / 10 = 4`, and `42 % 10 = 2`.

x86 gives you *both* results from one `div`, but `div` is a fussy instruction worth meeting carefully.
`div rcx` divides the **128-bit** value in `rdx:rax` by `rcx`, leaving the quotient in `rax` and the remainder in `rdx`.
Two things follow from that:

- It divides `rdx:rax`, not just `rax`, so you must clear `rdx` first (`xor rdx, rdx`) --- otherwise `div` treats leftover garbage as the high half of your number (and may crash).
- Like `mul`, its divisor comes from a register, not an immediate, so load the `10` into one.

So: put `value` in `rax`, `xor rdx, rdx`, `10` in `rcx`, then `div rcx`.
Now `rax` holds the tens and `rdx` holds the ones.
Turn each into a character the way `itoa_digit` did (add `'0'`) and store the two of them.

Write `itoa(value, buf)`: it takes the value (`0`-`99`) in `rdi` and a buffer pointer in `rsi`, writes the two characters to that buffer, and returns the count (`2`) in `rax`.
The tens come out first, which is the order you write them, so there's no reversing to do yet.
Remember to `.global itoa`.

Build and submit as before:

```console
hacker@dojo:~$ as -o your-solve.o your-solve.s
hacker@dojo:~$ ld -shared -o your-solve.so your-solve.o
hacker@dojo:~$ /challenge/check your-solve.so
```

Split with `div`, write the two digits, and score!
