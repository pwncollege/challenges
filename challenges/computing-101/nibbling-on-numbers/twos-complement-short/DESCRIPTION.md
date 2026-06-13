You've done two's complement one byte at a time, but nothing about it is special to 8 bits.
It works at any bit-width!

In this level, we'll practice twos complement on _16-bit values_.
Remember, `rax` and its friends are 64 bits wide, and they're also twos-complement, so you have a ways to scale up!

A 16-bit value can be as big as `2^16-1` when unsigned (65535), but if you interpret that binary value (`1111111111111111`) as a signed integer, you will get `-1`!
To interpret `1000000000000000` (unsigned 32768) as signed, you must subtract 65536 from it, resulting in -32768, which is the smallest signed value that can be expressed in 16 bits (with the largest signed value, `0111111111111111` being 32767).

This might be starting to get slightly confusing and, indeed, the different maximum values of signed versus unsigned numbers lead to all sorts of bugs and security vulnerabilities!

The size of these numbers makes manual math difficult, and we don't expect you to do these conversions in your head.
Our advice: do the unsigned conversion using a tool, then do the twos complement subtraction if it's signed.
One tool you can use is the `Python` programming language.
You don't have to program anything in it yet (though we'll get there), just use its interactive mode as a calculator.
For example, to convert the binary `1001111101011100`, you can do:

```console
hacker@dojo$ ipython
In [1]: 0b1001111101011100
Out[1]: 40796

In [2]: 40796 - 65536
Out[2]: -24740

In [3]: exit
hacker@dojo$
```

A few notes:

- `In [1]` is the input prompt for the `ipython` interactive python interpreter, and `Out [1]` is the result of the expression entered into `In [1]`.
- `0b` is Python's prefix to differentiate numbers written in binary from decimal (e.g., `0b101` is 5 and `101` is 101).

Run `/challenge/decode` directly, answer its questions, and get the flag!
