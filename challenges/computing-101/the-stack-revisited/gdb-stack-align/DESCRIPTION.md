You've used GDB to inspect registers, step through instructions, examine memory, and even cooperate with the debugger via `int3`.
This level brings back the alignment exercise from `mem-stack-align`, but now you have to do it from inside GDB too.

`/challenge/program` here is the same kind of binary as before: `argc` must be 1, and `(argv[0] & 0xFFFF)` must equal `0x5390`.
The new wrinkle is that **you have to solve it twice** --- once from a shell, once from inside GDB.
The flag only appears after both contexts have aligned `argv[0]` correctly.

First, do it from the shell --- exactly like in `mem-stack-align`:

```text
hacker@dojo:~$ env -i FOO=xxxxxxxx /challenge/program
```

Tune the length of `FOO` until the low 16 bits of `argv[0]` are `0x5390`.
On success, the program tells you to do it under GDB next.

Then do it inside GDB:

```text
(gdb) set exec-wrapper env -i FOO=xxxxxxxx
(gdb) run
```

`set exec-wrapper` tells GDB to prepend a command to the inferior's launch.
`env -i FOO=xxxxxxxx` is exactly what you did in the shell --- a clean environment with one variable --- so the final `execve` GDB makes is identical to the one your shell made.

If you skip `set exec-wrapper` and just `run`, you'll see `argv[0]` at a different address: GDB's process has its own environment (your shell's env, plus a few of GDB's own additions), and the inferior inherits all of it.
With `set exec-wrapper env -i FOO=xxxxxxxx`, you put GDB on the same footing as the bare shell launch, and your alignment math from the previous step works identically.

----

**NOTE:**
The order doesn't matter --- you can solve under GDB first and from the shell second.
The flag appears the moment both contexts have aligned `argv[0]` correctly.
