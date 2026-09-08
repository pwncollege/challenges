Your `atoi` tells its caller what number it found.
A scanner also needs to know where that number ended, so it can continue with the next part of the input.

You've already used both kinds of output together in `itoa`: it writes text through a pointer and returns a value in `rax`.
Write `parse_integer(input, destination)`: store the integer at `destination`, and return a pointer to the first input byte that is not part of the number.
That lets the caller continue reading from that address.

For example:

```text
input:       "-42asdf"
destination: -42
return:      pointer to the 'a' in the input
```

Keep your existing decimal parsing, including a leading minus sign and stopping at the first non-digit.
If a space ends the number, return a pointer to that space without skipping it.
If the number reaches the end of the string, return the address of the terminating NUL byte.
For example, `"-42 17"` returns a pointer to the space, and `"-42"` returns a pointer to its NUL byte.
Input starts with an optional `-` followed by one or more decimal digits, representing a value from `-2147483648` through `2147483647`.
A non-digit or NUL ends the number.
Store the result as a signed **64-bit integer**, even when its value fits in fewer bytes.

Use the calling convention from your earlier functions: `rdi` is the input pointer, `rsi` is the destination pointer, and `rax` is the returned input pointer.
Export `.global parse_integer`, preserve the callee-saved registers, and leave the input unchanged.

```console
hacker@dojo:~$ as --64 parser.s -o parser.o
hacker@dojo:~$ ld -shared parser.o -o parser.so
hacker@dojo:~$ /challenge/check parser.so
```
