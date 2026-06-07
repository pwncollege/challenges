Your two-digit `itoa` always wrote *two* characters.
But `7` isn't `07`, and `0` isn't `00` --- a number is written with no leading zeros, in as many digits as it actually has.

For values `0`-`99` that's one digit or two, and a single `div` tells you which.
Divide by 10 as before: the quotient is the tens digit, the remainder is the ones.
The new idea is what the quotient means: **if the quotient is `0`, there is no tens digit** --- the number was a single digit, so write just the ones character and stop.

```
7:   7 / 10 = 0 rem 7   ->  quotient 0, so write just "7"
42:  42 / 10 = 4 rem 2  ->  quotient 4, so write "42"
```

One value still needs care: `0` itself.
Its quotient is `0` too, but writing "nothing" is wrong --- write a single `'0'`.

That "stop once the quotient hits `0`" test is exactly what will drive the loop in the next level, where a number can have any number of digits.

Write `itoa(value, buf)` for `value` in `0`-`99`: write its decimal text (no leading zeros) to `buf`, and return how many characters you wrote (`1` or `2`) in `rax`.
Remember to `.global itoa`.

Build and submit as before:

```console
hacker@dojo:~$ as -o your-solve.o your-solve.s
hacker@dojo:~$ ld -shared -o your-solve.so your-solve.o
hacker@dojo:~$ /challenge/check your-solve.so
```

Drop the leading zero, return the real length, and score!
