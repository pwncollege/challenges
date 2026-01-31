So far, you've been reading the secret from the program's disassembly.
But what if the secret is hidden?

In this level, the disassembly is **censored**: the secret value is replaced with `CENSORED`.
However, even though you can't _read_ the value from the code, you can still _execute_ the code!
When the CPU executes `mov rdi, CENSORED`, it loads the actual secret value into the `rdi` register.

To execute a single instruction in GDB, use the `stepi` command (**step** one **i**nstruction, also abbreviated `si`):

```gdb
(gdb) stepi
```

Once you step past the `mov` instruction, we'll read the `rdi` register for you and show the secret value.
Submit it with `/challenge/submit-number`!
