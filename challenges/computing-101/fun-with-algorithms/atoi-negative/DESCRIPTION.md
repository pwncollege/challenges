Your `atoi` handles positive numbers.
But numbers can be negative, and a negative number arrives with a leading minus sign: the string `"-42"` is the four bytes `'-'`, `'4'`, `'2'`, NUL.

Extend your converter to handle that sign.
If the very first character is `'-'` (ASCII `0x2d`), remember that the result should come out negative, step past the sign, and convert the digits that follow exactly as before.
Then negate your total at the end.

Two's complement (which you met earlier) makes the negation a single instruction: `neg rax` turns a register into its negative.

```
"-42":  parse 42, then negate  ->  -42
```

A positive number has no sign character, so it should still convert just like the previous level.

Same contract as before: the string pointer comes in `rdi`, and your signed result goes in `rax`.
Build it, run `/challenge/check solve.so`, and grab the flag.
