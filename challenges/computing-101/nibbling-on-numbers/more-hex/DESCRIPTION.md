You're not limited to a single byte!
Just like decimal numbers, you can write as many hex digits as you need to represent more and more bytes --- **every two hex digits is one more byte**.
(A single hex digit, for the curious, is called a _nibble_ --- har har --- but we almost always work a whole byte at a time.)

Nothing new to learn here, just more of the same: split each byte's 8 bits into two groups of 4, turn each group into its hex digit, and write the bytes left to right. For example:

```
  1110 0011   0101 1010   1001 0000
   e    3      5    a      9    0
  -> 0xe35a90
```

Run `/challenge/convert`. This time it shows you multi-byte values in binary (grouped into bytes for readability); write each one back as one hexadecimal string. That's your first real _encoding_!
