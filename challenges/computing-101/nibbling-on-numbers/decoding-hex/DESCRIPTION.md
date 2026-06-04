So far you've **encoded** --- turned bits into hex. Now let's go the other way and **decode**: turn hex back into the bits it stands for.

It's the same mapping, just run in reverse. Each hex digit becomes its 4 bits, written out in order. Since a byte is two hex digits, decoding one byte means expanding two hex digits into 8 bits:

```
  0x   e      3
       1110   0011
  ->   11100011
```

This is exactly what a program does when it receives hex-encoded data: it turns each pair of hex digits back into the byte it represents before working with it.

Run `/challenge/convert`. It shows you a byte in hexadecimal; write each one back in binary. Decode them all to get the flag.
