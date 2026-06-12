Literal output, newline bytes, and escaped syntax give you the scan-and-write loop.
Now add the first marker: `%d`.

The `%` byte says "this is a marker".
The `d` byte says "take the next argument value, treat it as a signed decimal number, and print that number here."
The next command-line value starts at `argv[2]`.

```
argv[1]:  "value=%d"
argv[2]:  "-42"
output:   "value=-42"
```

When your scan reaches `%d`, skip both marker bytes, convert the next `argv` string with `atoi`, convert the resulting number back to text with signed `itoa`, and `write` those digits immediately.
Then continue scanning the format string.
For this level, the format string has at most one `%d` marker.
Keep handling ordinary text, `\n`, `\\`, and `%%` as before.

Build and submit as before:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ ./prog 'value=%d' -42
value=-42
hacker@dojo:~$ /challenge/check prog
```

Replace decimal markers as you scan.
