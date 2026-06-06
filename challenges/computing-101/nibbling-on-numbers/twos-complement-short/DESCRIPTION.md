You've done two's complement one byte at a time, but nothing about it is special to 8 bits.
It works at any bit-width!

In this level, we'll practice twos complement on _16-bit values_.
Remember, `rax` and its friends are 64 bits wide, and they're also twos-complement, so you have a ways to scale up!

A 16-bit value can be as big as `2^16-1` when unsigned (65535), but if you interpret that binary value (`1111111111111111`) as a signed integer, you will `-1`!
To interpret `1000000000000` (unsigned 32768) as signed, you must subtract 65536 from it, resulting in -32768, which is the smalllest signed value that can be expressed in 16 bits (with the largest signed value, `0111111111111111` being 32767).

This might be starting to get slightly confusing and, indeed, the different maximum values of signed versus unsigned numbers lead to all sorts of bugs and security vulnerabilities!
