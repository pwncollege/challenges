In `mem-stack-align`, you saw that the *launcher* shapes the inferior's stack: tuning the length of an environment variable in the shell shifts where `argv[0]` lands.
You aligned `(argv[0] & 0xFFFF) == 0x5390` from a clean shell launch with `env -i`.

`/challenge/program` here is the same kind of binary --- argc must be 1, `argv[0]` must be aligned to `0x5390` --- but **you have to solve it twice**: once from a shell, and once from inside GDB.
The flag appears only after both contexts have been satisfied.

Why? Because GDB is just another launcher --- and the point of this level is to feel that, viscerally, by doing the same alignment exercise from both sides.

----

**First, do it from the shell --- exactly like in `mem-stack-align`:**

```text
hacker@dojo:~$ env -i FOO=xxxxxxxx /challenge/program
```

Tune the length of `FOO` until `argv[0]` aligns to `0x5390`.
On success, the program tells you to do it under GDB next.

----

**Then do it inside GDB:**

```text
hacker@dojo:~$ gdb /challenge/program
(gdb) set exec-wrapper env -i FOO=xxxxxxxx
(gdb) run
```

`set exec-wrapper` tells GDB to prepend a wrapper command to the inferior's launch.
`env -i FOO=xxxxxxxx` is exactly what you did in the shell --- a clean environment with one variable --- so the *final* `execve` GDB makes is identical to the one your shell made.

If you skip `set exec-wrapper` and just `run`, you'll see `argv[0]` at a different address: GDB's process has its own environment (your shell's env, plus a few of GDB's own additions), and the inferior inherits all of it.
With `set exec-wrapper env -i FOO=xxxxxxxx`, you put GDB on the same footing as the bare shell launch --- and your alignment math from the previous step works identically.

When this second run aligns, the flag is printed.

----

**Why this matters:**

GDB is just *another launcher*.
The same trick that controls the inferior's stack from the shell (`env -i ...`) controls it from GDB (`set exec-wrapper env -i ...`).
This is not specific to environment variables --- whatever your shell can do at exec time (set args, redirect stdin, change cwd) GDB can also do, because in the end both of them are just calling `execve` with the parameters you specified.

The program you're debugging in GDB is the same program you'd run from the shell, and you can recreate any launch configuration in GDB that you can recreate in the shell.

----

**NOTE:** the order doesn't matter --- you can solve in GDB first and shell second --- but the flag only appears once both contexts have been aligned correctly.
