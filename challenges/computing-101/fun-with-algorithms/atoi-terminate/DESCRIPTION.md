Real input is messy.
A number embedded in a larger string isn't always followed by a tidy NUL --- it might be followed by a space, a letter, a comma, or anything else: `"42abc"`, `"100 200"`, `"7,"`.

A proper `atoi` reads digits until it sees something that *isn't* a digit, then stops --- whatever that non-digit is, the NUL included.

So change your stopping condition.
Instead of "stop at the NUL," the rule becomes "stop at the first byte that isn't `'0'`-`'9'`."

A handy one-shot test for a character `c`: compute `c - '0'`, then check whether the result is in the range `0`-`9` using an *unsigned* comparison.
Anything that isn't a digit --- punctuation, letters, a space, even the NUL (which becomes a huge number when you subtract `'0'` and read it unsigned) --- falls outside `0`-`9` and ends the loop:

```
cmp rcx, 9        ; rcx already holds (c - '0')
ja  done          ; unsigned "above 9" -> not a digit -> stop
```

Keep your sign handling from the previous level: a leading `'-'` still means negative, and everything after the number is simply ignored.

Same contract: string pointer in `rdi`, signed result in `rax`.

Build and submit as before:

```console
hacker@dojo:~$ /challenge/check your-solve.so
```

Stop at the first non-digit, return the value, and the flag is yours.
