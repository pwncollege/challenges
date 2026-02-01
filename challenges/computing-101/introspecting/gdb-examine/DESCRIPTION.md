In the last level, you could `stepi` to execute `pop rdi` and then `print $rdi` to read the secret.
This time, there's no `pop` at all --- the program just exits immediately:

```text
mov    rdi,0x0
mov    rax,0x3c
syscall             <- exit(0) --- the secret was never read!
```

The secret is still `argc`, and it's sitting right on top of the stack, but the program never loads it into a register.
You'll need to examine memory directly!

GDB's `x` (e**x**amine) command lets you look at the contents of memory.
As you learned earlier, the stack pointer (`$rsp`) starts out pointing right at `argc`, so you can read it with:

```text
x $rsp
```

Go and do that!

1. Start the program
2. Examine the top of the stack
3. Quit gdb and submit the value with `/challenge/submit-number`

----

**NOTE:**
`x` displays values in _hexadecimal_ by default.
You can change the display format by appending `/` to the command.
For example, if you'd rather see decimal, use `x/d $rsp`.
Either way, `/challenge/submit-number` accepts both hex (e.g., `0x2a`) and decimal (e.g., `42`).
