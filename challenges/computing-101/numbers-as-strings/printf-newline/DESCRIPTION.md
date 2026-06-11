Literal output can copy visible characters, but text also needs a way to name bytes that are awkward to type directly.
A newline is the classic example: it moves the terminal to the next line instead of drawing a visible symbol.

You've seen ASCII before: it assigns byte values to text characters and text controls.
The ASCII newline byte is `0x0a`, which is decimal `10`.

The common standard for writing special characters in a format string is the `\` prefix, and a newline is written as `\n`.
In this level, the two input bytes `\n` in the format string mean "write one output byte with value `0x0a`".
The backslash starts an **escape sequence**, and the next byte says which special byte to write.

```
argv[1]:  "hello\nworld"
output:   "hello"
          "world"
```

When your scan sees a backslash followed by `n`, skip both bytes and `write` one byte with value `0x0a`.
Keep supporting ordinary text.

When testing your program yourself, beware that some shell syntax can interpret `\n` before your program sees it.
Use plain quotes around the format string so your program receives the two bytes `\` and `n`, as in `./prog 'hello\nworld'`.

Build and submit as before:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ ./prog 'hello\nworld'
hello
world
hacker@dojo:~$ /challenge/check prog
```

Turn `\n` into a newline byte, and score!
