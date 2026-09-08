Your formatter uses a format string to turn values into text.
A scanner uses a format string to turn text back into values.
The `s` at the beginning of `sscanf` means its input comes from a string already in memory.

Start with the format `"%d"`.
Write `sscanf(input, format, destinations)`, calling your `parse_integer` to put the converted number in its destination.
The parser returns an input pointer; `sscanf` itself returns the number of values assigned, which is `1` here.

You've used arrays of pointers in `argv`.
Here, `destinations` points to an array whose entries point to writable output storage:

```text
destinations -> [pointer to the integer's storage]
                              |
                              v
                         8 writable bytes
```

The three arguments arrive in `rdi`, `rsi`, and `rdx`; the return value goes in `rax`.
The input starts with a valid decimal number, just as in the previous level.
Our scanner stores signed 64-bit integers and uses a destination array; this is our own assembly interface, rather than the C library's argument convention.

Export `.global sscanf` and `.global parse_integer`.
Keep both input strings unchanged and preserve the calling convention across your function calls.

```console
hacker@dojo:~$ as --64 scanner.s -o scanner.o
hacker@dojo:~$ ld -shared scanner.o -o scanner.so
hacker@dojo:~$ /challenge/check scanner.so
```
