Now your format string has syntax in it.
Backslash starts escape sequences such as `\n`, and percent will start format markers such as `%d`.

That creates a practical problem: sometimes the output should contain a real backslash or a real percent sign.
The usual formatter convention is to double the syntax byte.
The two input bytes `\\` write one output backslash byte, and the two input bytes `%%` write one output percent byte.

```
argv[1]:  "path\\file"
output:   "path\file"

argv[1]:  "progress: 100%%"
output:   "progress: 100%"
```

When your scan sees `\\`, skip both input bytes and `write` one backslash byte.
When your scan sees `%%`, skip both input bytes and `write` one percent byte.
Keep supporting ordinary text and `\n` escapes.

Build and submit as before:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ ./prog 'progress: 100%%'
progress: 100%
hacker@dojo:~$ /challenge/check prog
```

Turn doubled syntax bytes into one literal byte, and score!
