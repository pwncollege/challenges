Computers store data as bytes, which are made of bits.
The registers you're used to so far, such as `rax`, are 64 bits _wide_, meaning that they can hold values from 0 (all 0 bits) to `2^64-1` (all 1 bits).
But what if you wanted to store _negative_ numbers?

Early approaches to storing negative numbers included the use of a _sign_ bit: a positive decimal `5` might be stored as the byte `00000101`, while a negative `5` would be `10000101`.
This makes sense, but it has a very important problem: math.

Deep inside your computer's CPU is a subcomponent called an _Arithmetic Logical Unit_ (ALU), which is responsible for arithmetic.
This critical component needs to be very optimized, so the less complexity is needed to, say, add units, the better.
At the same time, the math needs to check out.
This leads to two issues:

1. A signed bit system has _two_ different values for zero: `00000000` (positive zero) and `10000000` (negative zero). This is terrible for many reasons, including having to complicate the ALU.
2. In a signed bit system, different arithmetic algorithms need to be used for signed versus unsigned numbers. You can add `00000010` (decimal `2`) and `00000001` (decimal `1`) easily with normal binary math, but `10000010` (decimal `-2`) and `00000001` (decimal `1`) need to instead be modeled partially as subtractive.

This is not great.
Luckily, some smart minds came up with a brilliant scheme called [Twos Complement](https://en.wikipedia.org/wiki/Two%27s_complement).
Twos complement solves both problems by modeling half of the bit space as negative _in a way compatible with unsigned arithmetic_.
Consider this subtraction:

```text
  00000001    a positive 1
- 00000010    a positive 2 (being subtracted)
```

There aren't enough bits to service this subtraction, so we introduce a _borrow_ bit:

```text
  1 00000001    a positive 1 (with a borrow bit)
- 0 00000010    a positive 2 (being subtracted)
  ----------
  0 11111111    the result of the normal *sign-agnostic* subtraction
```

So `11111111` *is* `-1`: add it to `1` and they cancel, with the leftover bit falling off the end of the byte and vanishing.
This has a few advantages:

1. The top bit is still the _sign bit_: if it's set, the value is negative! Very easy to test.
2. There is only one zero: `00000000`.
3. Arithmetic works exactly normally for both signed and unsigned numbers.

The downside is the slight human complexity: the actual magnitude (e.g., value after the sign) of a negative number is the unsigned byte value _minus 256_.
In the above `11111111`, it's `255 - 256 = -1`.
A bit complex, but you'll get the idea eventually.
Interestingly, if you treat the value as _unsigned_, you can happily use it as 255 in the arithmetic you want, and everything will still work out!

Now, put this to use.
This challenge will force you to understand twos-complement on bytes.
Run `/challenge/decode` and get the flag!
