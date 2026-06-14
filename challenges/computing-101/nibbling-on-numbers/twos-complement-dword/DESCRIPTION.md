Let's go wider!
We'll try 4 bytes, 32 bits.
Use the same `python3 -q` calculator workflow from the 16-bit level: convert the binary as unsigned first, then subtract `2**32` if the top bit is set.
The maximum unsigned value of this, `11111111 11111111 11111111 11111111`, is `2**32-1`, or `4,294,967,295`.
The maximum signed value, `01111111 11111111 11111111 11111111`, is `2**31-1`, which is `2,147,483,647`, and the minimum signed value, `10000000 00000000 00000000 00000000`, is `-2**31`, which is `-2,147,483,648`.

Run `/challenge/decode` and get the flag!
