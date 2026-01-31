In the previous level, we automatically read the register value for you after you stepped.
Now it's your turn!

The disassembly is still censored, so you'll need to:
1. Start the program with `starti`
2. Step one instruction with `stepi` (or `si`)
3. Read the register yourself with `print $rdi`

The `print` command displays the value of an expression.
Register names in GDB are prefixed with `$`, so you can read `rdi` like this:

```gdb
(gdb) print $rdi
$1 = 1337
```

Then submit the value with `/challenge/submit-number`.
