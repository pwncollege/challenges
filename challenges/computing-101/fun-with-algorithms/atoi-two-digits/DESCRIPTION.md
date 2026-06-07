You can decode one digit with `atoi_digit`.
A two-digit number is just two of those, combined by *place value*: in `"42"`, the `4` is in the tens place and the `2` is in the ones place, so the value is `4 * 10 + 2 = 42`.
This is the algorithm we'll use to compute it in this level.

Here, you'll write **two** functions:

- `atoi_digit(s)` --- exactly as before: the value of the single digit at `s`. You can (and should!) reuse your solution from the previous challenge.
- `atoi(s)` --- takes a pointer to a _two-character_ number and returns its value, by decoding each character with `atoi_digit` and combining them as `first * 10 + second`.

Both are real functions the grader calls, so both must follow the calling convention.
That means that if you use any _callee-saved registers_, you must properly restore them before returning.
And, since you're also _calling_ `atoi_digit` from `atoi`, you must be careful to properly handle any _caller-saved_ registers as well.

As before, each function takes its argument in `rdi` and returns its result in `rax`.

Now, how do you multiply?
x86's multiply instruction is `imul`.
It has a few different ways to use it, but we'll use it like we used `add`: `imul rax, 10` multiplies `rax` by `10` in place (`rax = rax * 10`), so scaling the tens digit up by a place is a single instruction.
Of course, `imul` can use other registers than `rax`: for example, `imul rbx, 10` multiplies `rbx` by `10`.

Build and submit as before, with both `atoi_digit` and `atoi` functions:

```console
hacker@dojo:~$ /challenge/check your-solve.so
```

Multiply by ten, add the ones, and the flag is yours.
