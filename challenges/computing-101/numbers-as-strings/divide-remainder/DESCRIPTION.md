Your `itoa_digit` handled one digit, but a number such as `42` has two decimal places that must be separated before either digit can become text.
Dividing by `10` does both jobs: the quotient is the tens digit, and the remainder is the ones digit.
For `42`, the quotient is `4` and the remainder is `2`.

On x86-64, the unsigned division instruction is `div`.
Unlike the `imul rax, 10` form you used earlier, `div` does not take the divisor as an immediate value.
The form you need is `div rcx` after placing `10` in `rcx`.
Unlike `imul`, `div` uses fixed registers for its other values.
It divides the combined 128-bit value in `rdx:rax` by its operand, puts the quotient in `rax`, and puts the remainder in `rdx`.

For the ordinary 64-bit values in this level, the dividend belongs in `rax` and the high half in `rdx` must be zero before the division.
If `rdx` still contains an unrelated value, it becomes part of the dividend and can produce the wrong result or a division error.

Write a function called `solve` that takes a two-digit unsigned value from `10` through `99` in `rdi`.
Use `div` to split it into its tens and ones digits, add those digits together, return their sum in `rax`, and export the function with `.global solve`.
For example, `solve(42)` must return `6`.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```
