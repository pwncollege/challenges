Next, we'll learn about how to print out the values of registers.

You can see the values for all your registers with `info registers`. Alternatively, you can also just print a particular
register's value with the `print` command, or `p` for short. For example, `p $rdi` will print the value of $rdi in
decimal. You can also print its value in hex with `p/x $rdi`.

In order to solve this level, you must figure out the current random value of register r12 in hex.

As before, start the challenge, invoke the `run` gdb command, then follow the instructions.
When you've printed out what you need, remember to `continue` to move on to the next step of the challenge!

----
**RELEVANT DOCUMENTATION:**
- gdb's [run](https://sourceware.org/gdb/current/onlinedocs/gdb#Starting) command
- gdb's [continue](https://sourceware.org/gdb/current/onlinedocs/gdb#Continuing-and-Stepping) command
- gdb's [info](https://sourceware.org/gdb/current/onlinedocs/gdb#Registers) command
- gdb's [print](https://sourceware.org/gdb/current/onlinedocs/gdb#Data) command
