Time to put the reading above into practice.

The key fact: a single hex digit is exactly 4 bits, so a byte --- 8 bits --- is just two hex digits.
To turn a byte from binary into hex, split its 8 bits into two groups of 4 and look each group up:

```
  1110 0011        the byte, in binary
   e    3          each group of 4 bits -> one hex digit
  ->  0xe3
```

Run `/challenge/convert`. It shows you bytes in binary; write each one back in hexadecimal.
(You can include the `0x` prefix or leave it off --- both work.)
Get them all and you'll have the flag.
