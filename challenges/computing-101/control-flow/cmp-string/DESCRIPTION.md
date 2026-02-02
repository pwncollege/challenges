In the previous challenge, you used `cmp` and `jne` to check a single character and branch to a failure path.
But checking one character always sufficient: passwords, commands, and filenames are all _strings_ of multiple characters.

The good news: you already know everything you need to check a whole string!
You simply chain multiple `cmp` / `jne` pairs, one for each character, all jumping to the same `fail` label:

```asm
mov rax, [rsp+16]       ; load argv[1] pointer

cmp BYTE PTR [rax], 'Y'
jne fail

cmp BYTE PTR [rax+1], 'E'
jne fail

cmp BYTE PTR [rax+2], 'S'
jne fail
```

Each comparison checks one character of the string.
Remember from the [Computer Memory](/computing-101/computer-memory) module that `[rax+1]` accesses the byte _one past_ the address in `rax`, `[rax+2]` is two past, and so on.
Since strings are stored as contiguous bytes in memory, `[rax]` is the first character, `[rax+1]` is the second, `[rax+2]` is the third, etc.

If any character doesn't match, `jne` immediately jumps to `fail` --- the program doesn't bother checking the rest.
Only if _all_ comparisons pass (all characters match) does execution fall through to the success path.

This is how many string comparisons work at the lowest level: compare byte by byte, bail out on the first mismatch.

Now, you will practice this.
Write a program that checks whether the first argument starts with the string `"pwn"`:

1. Load the pointer for the first argument from `[rsp+16]`.
2. Compare byte at offset 0 against `'p'` --- `jne fail` if it doesn't match.
3. Compare byte at offset 1 against `'w'` --- `jne fail` if it doesn't match.
4. Compare byte at offset 2 against `'n'` --- `jne fail` if it doesn't match.
5. Implement the success path: `exit(0)`.
6. Implement the `fail:` label with `exit(1)`.
