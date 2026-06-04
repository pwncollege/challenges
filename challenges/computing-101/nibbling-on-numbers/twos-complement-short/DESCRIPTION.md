You met two's complement one byte at a time. Nothing about it was special to 8 bits --- the exact same rule scales to any width.

A **short** is 16 bits (two bytes). The top bit, bit 15, is still the sign. A positive short reads the same whether you call it signed or unsigned; a negative short's signed value is its unsigned value **minus 2¹⁶ = 65536**. For example, the 16-bit pattern `11111111 11111111` is `65535` unsigned, or `-1` signed --- exactly the byte story, just with more bits (and the same carry-off-the-top reason behind it).

Run `/challenge/decode`. It shows you a positive short and a negative one, printed in two 8-bit groups so the bits are easy to read. Give the positive one's value, and for the negative one give **both** readings: first the unsigned value (add up all 16 bits), then the signed two's-complement value (that unsigned value minus 65536).
