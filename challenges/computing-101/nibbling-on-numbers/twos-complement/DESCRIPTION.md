Every number you've worked with so far has been zero or positive.
But programs need negatives too --- and a register is just 64 bits, all equal, with no special slot for a minus sign. So how can a pile of bits mean `-5`?

The scheme nearly every CPU uses is called **two's complement**, and the cleverest way to understand it is to ask: *which* bit patterns should be the negatives? We want one rule above all --- `x + (-x)` must come out to `0`. Watch what that forces. In a single byte, `1` is `00000001`; for some pattern to deserve the name `-1`, adding it to `00000001` has to give zero:

```
  00000001    1
+ 11111111    -1
  --------
 100000000    the 1 carries off the top of the byte, into nowhere...
  00000000    ...leaving zero.
```

So `11111111` *is* `-1`: add it to `1` and they cancel, with the leftover bit falling off the end of the byte and vanishing. Work it out for any value and you reach one simple rule: **the top bit is the sign.** If the highest bit is set, the number is negative, and its value is exactly *(the unsigned reading) − 256*.

That's why the same byte is two numbers at once. `11111111` is `255` if you read all eight bits as a plain magnitude, or `-1` if you read it as two's complement. `10000000` is `128`, or `-128`. The bits don't know which they are --- only your interpretation decides. (For a *positive* byte the two readings happen to be the same, because subtracting 256 only comes into play when the top bit is set.)

So let's see if you can do the interpreting. Run:

```
hacker@dojo:~$ /challenge/decode
```

It will show you several bytes, some positive and some negative, and ask you to read each one:

- For a **positive** byte (top bit `0`), just give its value --- add up the bits.
- For a **negative** byte (top bit `1`), it asks for *both* readings: first the **unsigned** value (the bits added up), then the **signed** two's-complement value (that same unsigned value, minus 256).

Read every byte correctly and you get the flag. Give the unsigned value where the signed one was asked for --- the classic mistake --- and it'll catch you, because those bits mean two different things.
