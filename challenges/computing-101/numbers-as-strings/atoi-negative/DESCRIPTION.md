Your `atoi` handles positive numbers.
But numbers can be negative, and a negative number arrives with a leading minus sign: the string `"-42"` is the four bytes `'-'`, `'4'`, `'2'`, NUL.

Extend your converter to handle that sign.
If the very first character is `'-'` (ASCII `0x2d`), remember that the result should come out negative, step past the sign, and convert the digits that follow exactly as before.
Then negate your total at the end.
Of course, a positive number has no sign character, so it should still convert just like the previous level.

There are two ways you can negate a number: `neg rax` turns a register into its negative, and `imul rax, -1` does the same.
Pick the one you like!
