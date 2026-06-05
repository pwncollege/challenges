The first three levels had you _read_ bits as a signed number. Now let's go the other way: given a number, **write** its two's-complement bits.

For a zero-or-positive number, that's just its plain binary, padded with leading zeros to fill the byte. For a negative number, recall the rule from the very first level --- the `n`-bit two's-complement pattern of a negative value is the same bits as the unsigned number `(value + 2ⁿ)`. In a byte (8 bits), that means adding 256:

```
  -5   ->   -5 + 256 = 251   ->   11111011
  42   ->                         00101010
```

(Equivalently: flip the bits of `+5` and add one --- same answer, `11111011`. Either way of thinking about it works.)

Run `/challenge/encode`. It gives you numbers --- some negative, some not --- and you write each one as **8-bit two's-complement binary**. Encode them all to get the flag.
