Your `atoi` tells its caller what number it found.
A scanner also needs to know where that number ended, so it can continue with the next part of the input.

You've already used both kinds of output together in `itoa`: it writes text through a pointer and returns how many bytes it wrote.
Give your integer parser the same arrangement.
Write `parse_integer(input, destination)`: store the integer at `destination`, and return the number of input bytes consumed.

For example:

```text
input:       "-42 rest"
destination: -42
return:      3
```

Keep your existing decimal parsing, including a leading minus sign and stopping at the first non-digit.
The count includes the sign and any leading zeroes, but excludes the character that ended the number.
Input starts with an optional `-` followed by one or more decimal digits, representing a value from `-2147483648` through `2147483647`.
A non-digit or NUL ends the number.
Store the result as a signed **64-bit integer**, even when its value fits in fewer bytes.

Use the calling convention from your earlier functions: `rdi` is the input pointer, `rsi` is the destination pointer, and `rax` is the returned count.
Export `.global parse_integer`, preserve the callee-saved registers, and leave the input unchanged.

```console
hacker@dojo:~$ as --64 parser.s -o parser.o
hacker@dojo:~$ ld -shared parser.o -o parser.so
hacker@dojo:~$ /challenge/check parser.so
```
