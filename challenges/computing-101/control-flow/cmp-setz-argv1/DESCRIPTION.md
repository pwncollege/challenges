Now let's apply what you've learned to check a specific character in a command-line argument.

Recall from the [Stack](/computing-101/the-stack) module that `[rsp+16]` holds a _pointer_ to `argv[1]` --- the first command-line argument.
To actually look at the argument text, you first need to load that pointer into a register:

```asm
mov rax, [rsp+16]
```

Now `rax` holds the _address_ of the argument string.
The first character of that string lives at `[rax]`, the second at `[rax+1]`, and so on.

To check whether the first character is, say, `'p'`:

```asm
cmp BYTE PTR [rax], 'p'
```

This reads one byte from the address in `rax` and compares it against the ASCII value of `'p'`.
Remember: `BYTE PTR` tells the CPU you're working with a single byte, not a full 64-bit value.
You learned this back in the [Output and Input](/computing-101/hello-hackers) module when you built strings on the stack byte by byte.

After the `cmp`, the Zero Flag reflects whether they matched, and you can capture that result with `setz dil`, just like before.

Your challenge: write a program that checks whether the first character of `argv[1]` is `'p'`.
Exit with `1` if it is, `0` if it isn't.

Your program should use 5 instructions:

1. Load the `argv[1]` pointer from `[rsp+16]` into a register.
2. Compare `BYTE PTR` at that address against `'p'`.
3. Use `setz dil` to capture the result.
4. Set up the `exit` syscall number.
5. `syscall`.
