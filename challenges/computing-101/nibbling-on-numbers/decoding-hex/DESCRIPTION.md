So far you've **encoded** binary data into hex. Now let's go the other way and **decode** it: that is, turn hex back into the bits it stands for.

It's the same mapping, just run in reverse.
Each hex digit becomes its 4 bits, written out in order.
Since a byte is two hex digits, decoding one byte means expanding two hex digits into 8 bits:

```
0x   0      a
     0000   1010
->   00001010
```

This is exactly what a program does when it receives hex-encoded data: it turns each pair of hex digits back into the byte it represents before working with it.
Write out the full 8 bits, leading zeros and all --- each hex digit is always exactly 4 of them.

Run `/challenge/convert` and get the flag!
