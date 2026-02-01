In previous levels, the secret was hidden in the program's code (a hardcoded `mov` instruction).
This time, the secret comes from the program's *runtime state*: it's the argument count (`argc`), which lives on the stack.

The program pops this value off the stack with `pop rdi`, but then immediately overwrites `rdi` with 0 before exiting:

```text
pop    rdi          <- reads argc from the stack into rdi
mov    rdi,0x0      <- overwrites rdi with 0!
mov    rax,0x3c
syscall             <- exit(0) --- the secret is gone!
```

The code is fully visible, and nothing is censored, but you can't determine the secret just by reading the disassembly because `argc` depends on how many arguments the program was launched with.
In this level, GDB handles that for you, but in the future, we'll show you how to set the program's arguments in gdb as well!

For now, you'll need to:
1. Start the program.
2. Step one instruction to execute just `pop rdi`
3. `print` the resulting value in `rdi` before it gets overwritten
4. Quit gdb and then submit the value with `/challenge/submit-number`.
