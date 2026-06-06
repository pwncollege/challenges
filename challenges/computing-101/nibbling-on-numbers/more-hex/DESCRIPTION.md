Like decimal numbers, you can add arbitrary amounts of them to represent more and more bytes.
Every two hex digits are one additional byte.
One hex digit, for those curious, is called a _nibble_ (har har!), but this is not used when specifying data.
We almost always work with data on the _byte_ level, not less.

We'll practice this in this challenge.
Split each byte's 8 bits into two groups of 4, turn each group into its hex digit, and write the bytes left to right. For example:

```
1110 0011   0101 1010   1001 0000
 e    3      5    a      9    0
-> 0xe35a90
```

Now it's your turn: run `/challenge/convert` and go earn that flag!
