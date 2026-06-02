A common stack-related snafu is the shift in stack addresses that happens when launching a program under gdb.
By default, gdb passes its own environment (your shell's env, plus a few of gdb's own additions) to the debugged program, and these extra environment variables shift the stack to the left, so `argv[0]` ends up at a different address than it does when you run the program straight from your shell.
This isn't so important right now, but it becomes a big bother later on when you're trying to figure out why your bit-precise exploit code works in gdb but not on a target running normally.
In those cases, learning to "synchronize" the two environments is important.

This challenge will teach you the basics: making the addresses outside of gdb line up better with the addresses inside gdb.

1. Run `/challenge/program` under gdb (`gdb /challenge/program`, then `run`).
   The program records its own `argv[0]` as your target.
2. Quit gdb. Run `/challenge/program` from your shell --- it'll tell you how far off your shell-context `argv[0]` is from the target.
3. Use an environment variable to "pad" your shell environment until `argv[0]` lands at the gdb-captured target.
4. Flag!
