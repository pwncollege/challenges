Format strings also need a way to name bytes that are awkward to type directly.
A newline is the classic example.

The common standard for specifying special characters is the `\` prefix, and a newline is typically `\n`.
In this level, the two bytes `\n` in the format string mean "write one newline byte".
The backslash starts an **escape sequence**, and the next byte says which special byte to write.

```
argv[1]:  "hello\nworld"
output:   "hello"
          "world"
```

When your scan sees a backslash followed by `n`, skip both bytes and `write` one byte with value `10`.
Keep supporting ordinary text, `%d`, and `%s`.

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
