Same rule again, wider still.

A **dword** ("double word") is 32 bits --- four bytes. The top bit, bit 31, is the sign. A positive dword reads identically signed or unsigned; a negative dword's signed value is its unsigned value **minus 2³² = 4294967296**. So `11111111 11111111 11111111 11111111` is `4294967295` unsigned, or `-1` signed. The number of bits keeps growing, but the idea never changes: the high bit is the sign, and a negative value is the unsigned reading minus 2 to the width.

Run `/challenge/decode`. It shows you a positive dword and a negative one, printed in four 8-bit groups. Give the positive one's value, and for the negative one give **both** readings: the unsigned value (all 32 bits added up), then the signed two's-complement value (that unsigned value minus 4294967296).
