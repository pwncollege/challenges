`\n` gives one named ASCII byte: newline, `0x0a`.
For arbitrary bytes, use a hex escape: `\xNN`.

You've seen hex before: two hex digits describe one byte.
Here, the `\x` starts the escape, and the next two hex digits are the byte value to write.

```
format bytes:  "\x41"
hex value:      0x41
output byte (ascii):    "A"
```

Be careful about the conversion step: the format string contains ASCII characters, not numeric hex values yet.
For `\x4a`, your program sees four input bytes: backslash, `x`, `4`, and `a`.
After recognizing the `\x`, the conversion uses the ASCII bytes for `4` and `a`.
First convert each ASCII hex character into a 4-bit number, called a nibble.
For `0` through `9`, subtract the ASCII value of `0` to get `0` through `9`.
For `a` through `f`, subtract the ASCII value of `a` and add `10`; for `A` through `F`, subtract the ASCII value of `A` and add `10`.
Then put the first nibble in the high half of the byte (using left shift, which you learned earlier!) and the second nibble in the low half: `(first << 4) | second`.

```
format text:      \ x 4 a
hex digits:           4 10
combined byte:        (4 << 4) | 10 = 0x4a
output byte:          "J"
```

When your scan sees `\xNN`, convert the two hex digits into one byte and `write` that byte.
Keep supporting ordinary text, `%d`, `%s`, and `\n`.

Build and submit as before:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ ./prog 'byte=\x2a'
byte=*
hacker@dojo:~$ /challenge/check prog
```

Decode the hex byte escape, write it, and score!
