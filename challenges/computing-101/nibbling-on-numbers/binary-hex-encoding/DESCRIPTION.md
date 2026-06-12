Time to put the reading above into practice.

The key fact: a single hex digit is exactly 4 bits, so a byte --- 8 bits --- is just two hex digits.
To turn a byte from binary into hex, split its 8 bits into two groups of 4 and look each group up:

```
11100011     the byte, in binary
1110 0011    the byte, in binary, split into two groups of 4 bits
 e    3      each group of 4 bits -> one hex digit
->  0xe3     the hex!
```

Run `/challenge/convert` and get the flag!
