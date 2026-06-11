`\n` gives one named ASCII byte: newline, `0x0a`.
For arbitrary bytes, use a hex escape: `\xNN`.

You've seen hex before: two hex digits describe one byte.
Here, the `\x` starts the escape, and the next two hex digits are the byte value to write.

```
format bytes:  "\x41"
hex value:      0x41
output byte (ascii):    "A"
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
