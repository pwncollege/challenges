Literal output is byte-for-byte copying: read one byte from the format string, then `write` that byte.
So far, those bytes have all drawn visible characters.

Text also has control bytes.
A newline is the byte that moves the terminal to the next line.
You've seen ASCII before: the ASCII newline byte is `0x0a`, which is decimal `10`.

In this level, the format string can already contain newline bytes.
Do not treat them as special syntax.
Copy each newline byte just like any other byte, and `write` will move the output to the next line.

Keep supporting ordinary visible text.

Build and submit as before:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ /challenge/check prog
```

Copy newline bytes as part of the format string.
