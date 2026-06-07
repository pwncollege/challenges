You can decode one digit with `atoi_digit`.
A two-digit number is just two of those, combined by *place value*: in `"42"`, the `4` is in the tens place and the `2` is in the ones place, so the value is `4 * 10 + 2 = 42`.

That `* 10` is the new idea --- shift the first digit up a place, then add the second.

In this level you'll write **two** functions:

- `atoi_digit(s)` --- exactly as before: the value of the single digit at `s`.
- `atoi(s)` --- takes a pointer to a *two-character* number and returns its value, by decoding each character with `atoi_digit` and combining them as `first * 10 + second`.

Both are real functions the grader calls, so both must follow the calling convention.
And note `atoi` now *calls* `atoi_digit` --- the argument registers don't survive a call, so stash anything you'll still need (like the string pointer) somewhere that does.

Each function takes its argument in `rdi` and returns its result in `rax`.

Build and submit as before:

```console
hacker@dojo:~$ /challenge/check your-solve.so
```

Multiply by ten, add the ones, and the flag is yours.
