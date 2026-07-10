In the previous level, you used `print` to read a register's value.
GDB can also change a register while the program is stopped.

The `set` command assigns a new value to a register:

```gdb
(gdb) set $rax = 42
```

As with `print`, prefix the register name with `$`.

In this level, you will need to:

1. Start the program with `starti` and step past its first instruction.
2. Set `rdi` to `1337` and step once more.
3. Print the resulting secret number, then submit it with `/challenge/submit-number`.

Run `gdb /challenge/debug-me` and change that register!
