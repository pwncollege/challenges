You've taken text input and converted it to a number, but real programs also have to _output_ numbers as text.
This inverse of `atoi` is called `itoa` (integer to ASCII).
Here, we'll start building it the same way, first with one digit, then moving on!

In the reverse of `atoi`, a digit's character is just its value plus `'0'` (`0x30`).
So if `'7'` (the ASCII character) became `7` (the value) by subtracting `0x30`, then the same way, `7` (the value) would become `'7'` (the ASCII character) by adding `0x30`.

```
7  ->  7 + 0x30  =  0x37  =  '7'
```

We'll start with `itoa_digit`.
Your `itoa_digit` gets a value in `rdi` (a single digit, `0`-`9`) and returns its ASCII character in `rax`.
Remember to `.global itoa_digit` so the challenge can find it.

Build and submit it as a library, add `0x30`, and return the character.
