In [Divide and Remainder](/computing-101/numbers-as-strings/divide-remainder), you split a two-digit number into its tens digit in `rax` and its ones digit in `rdx`.
Now you will turn both digits back into text and write them into an output buffer.

Your `itoa_digit` returned one character directly in `rax`.
A string is instead written as a sequence of bytes in memory, so the caller gives `itoa` a pointer to writable memory in `rsi`.
Each ASCII character is one byte, so each store must write only the low byte of the register holding that character.

The low byte of `rax` is named `al`, and the low byte of `rdx` is named `dl`.
For example, this stores only the character in `al`, leaving the surrounding bytes untouched:

```asm
mov BYTE PTR [rsi], al
```

Write `itoa(value, buf)`, with a value from `10` through `99` in `rdi` and the buffer pointer in `rsi`.
Use the division you just practiced, convert both digits to their ASCII characters, write the tens character to `buf[0]` and the ones character to `buf[1]`, and return `2` in `rax`.
Export the function with `.global itoa`.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o your-solve.o your-solve.s
hacker@dojo:~$ ld -shared -o your-solve.so your-solve.o
hacker@dojo:~$ /challenge/check your-solve.so
```
