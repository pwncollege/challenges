A critical part of dynamic analysis is getting your program to the state you are interested in analyzing.
So far, these challenges have automatically set breakpoints for you to pause execution at states you may be interested in analyzing.
It is important to be able to do this yourself.

There are a number of ways to move forward in the program's execution.
You can use the `stepi <n>` command, or `si <n>` for short, in order to step forward one instruction.
You can use the `nexti <n>` command, or `ni <n>` for short, in order to step forward one instruction, while stepping over any function calls.
The `<n>` parameter is optional, but allows you to perform multiple steps at once.
You can use the `finish` command in order to finish the currently executing function.
You can use the `break *<address>` parameterized command in order to set a breakpoint at the specified-address.
You have already used the `continue` command, which will continue execution until the program hits a breakpoint.

While stepping through a program, you may find it useful to have some values displayed to you at all times.
There are multiple ways to do this.
The simplest way is to use the `display/<n><u><f>` parameterized command, which follows exactly the same format as the `x/<n><u><f>` parameterized command.
For example, `display/8i $rip` will always show you the next 8 instructions.
On the other hand, `display/4gx $rsp` will always show you the first 4 values on the stack.
Another option is to use the `layout regs` command.
This will put gdb into its TUI mode and show you the contents of all of the registers, as well as nearby instructions.

In order to solve this level, you must figure out a series of random values which will be placed on the stack.
As before, `run` will start you out, but it will interrupt the program and you must, carefully, continue its execution.

You are highly encouraged to try using combinations of `stepi`, `nexti`, `break`, `continue`, and `finish` to make sure you have a good internal understanding of these commands.
The commands are all absolutely critical to navigating a program's execution.

----
**RELEVANT DOCUMENTATION:**
- gdb's [run](https://sourceware.org/gdb/current/onlinedocs/gdb#Starting) command
- gdb's [continue](https://sourceware.org/gdb/current/onlinedocs/gdb#Continuing-and-Stepping) command
- gdb's [info](https://sourceware.org/gdb/current/onlinedocs/gdb#Registers) command
- gdb's [print](https://sourceware.org/gdb/current/onlinedocs/gdb#Data) command
- gdb's [examine](https://sourceware.org/gdb/current/onlinedocs/gdb#Memory) command
- gdb's [break](https://sourceware.org/gdb/current/onlinedocs/gdb#Set-Breaks) command
- gdb's [display](https://sourceware.org/gdb/current/onlinedocs/gdb#Auto-Display) command
- gdb's [various stepping commands](https://sourceware.org/gdb/current/onlinedocs/gdb#Continuing-and-Stepping) command (that whole section)

**NOTE:**
This challenge will require you to _read_ and _understand_ assembly!
Don't worry, this skill will come in quite handy later in pwn.college.
