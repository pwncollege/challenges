Now add `%s`, the marker for inserting a string.
This is like `%d`, except the next `argv` value is already text, so you do not need `atoi` or `itoa`.

For `%s`, take the next command-line string, find its length, and `write` its bytes.
For `%d`, keep doing the number conversion from the previous levels.
Each marker consumes the next command-line value in order.
The format string is the only string with formatter syntax.
If the argument for `%s` contains bytes like `\` or `%`, copy them literally instead of treating them as escapes or markers.

```
argv[1]:  "%s has %d flags"
argv[2]:  "hacker"
argv[3]:  "3"
output:   "hacker has 3 flags"
```

```
argv[1]:  "%s"
argv[2]:  "LITERAL\WITH\SLASHES"
output:   "LITERAL\WITH\SLASHES"
```

This means your program now tracks two positions: where you are in the format string, and which `argv` value should be consumed next.

Build and submit as before:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ ./prog '%s has %d flags' hacker 3
hacker has 3 flags
hacker@dojo:~$ /challenge/check prog
```

Consume values in order and write each piece on demand.
