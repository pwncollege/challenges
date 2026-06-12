Now your format string has syntax in it.
Backslash starts escape sequences, and percent is also a syntax byte in formatters.

An escape sequence is a way to name an output byte using bytes that are easier to type.
For example, the two input bytes `\n` write one output newline byte, `0x0a`.

Syntax bytes create another practical problem: sometimes the output should contain a real backslash or a real percent sign.
The usual formatter convention is to double the syntax byte.
The two input bytes `\\` write one output backslash byte, and the two input bytes `%%` write one output percent byte.

```
argv[1]:  "hello\nworld"
output:   "hello"
          "world"

argv[1]:  "path\\file"
output:   "path\file"

argv[1]:  "progress: 100%%"
output:   "progress: 100%"
```

When your scan sees `\n`, skip both input bytes and `write` one newline byte.
When your scan sees `\\`, skip both input bytes and `write` one backslash byte.
When your scan sees `%%`, skip both input bytes and `write` one percent byte.
Keep supporting ordinary text and literal newline bytes.

Build and submit as before:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ ./prog 'progress: 100%%'
progress: 100%
hacker@dojo:~$ /challenge/check prog
```

Handle escape syntax as you scan.
