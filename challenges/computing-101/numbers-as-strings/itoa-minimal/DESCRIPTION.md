Your two-digit `itoa` always wrote *two* characters.
But `7` isn't `07`, and `0` isn't `00` --- numbers tend to be written with no leading zeros, in as many digits as it actually has.
In this level, we'll strip the leading zeroes from our translation on the path to a nice `itoa`!

We'll still deal with values `99` and less, so a single `div`.
Divide by 10 as before: the quotient is the tens digit, the remainder is the ones.
If the quotient is `0`, there is no tens digit, and we can drop the leading zero and output just the remainder.
For example:

```
7:   7 / 10 = 0 rem 7   ->  quotient 0, so write just "7"
42:  42 / 10 = 4 rem 2  ->  quotient 4, so write "42"
```

One value still needs care: `0` itself.
Its quotient is `0` too, but writing "nothing" is wrong, so we write a single `'0'`.

The rest is the same:
Write `itoa(value, buf)` for `value` in `0`-`99`: write its decimal text (no leading zeros) to `buf`, and return how many characters you wrote (`1` or `2`) in `rax`.

----

**Note:**
The "check if the quotient is `0`" test will be useful in the next level, where we'll finally support longer numbers!
Keep it in mind!
