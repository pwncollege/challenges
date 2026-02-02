So far, the debugging you've done has been **preemptive**: _you_ (the debugger) started the program with `stepi`, which immediately forces it to stop and let you debug it, without the program necessarily being aware of it.
In this challenge, we'll learn another model for this, where the program decides when the debugger stop happens.
We'll call this **cooperative** debugging.

On our now-familiar x86 architecture, the program can signal a desire to be debugged by using the `int3` instruction.
If a debugger is attached when `int3` is executed, it stops the program.
This is called a program **breakpoint**.

Later, we'll learn how to set breakpoints from the debugger itself, going back to the preemptive model.
But in this challenge, the checker will run your program under gdb and expect your program to trigger its own breakpoint.
To do this, rather than using `starti` to start your program and immediately stop it, we'll use gdb's `run` command, which will simply run it until a breakpoint is hit!

When your program executes `int3`, gdb will break and the checker script will inspect `$rdi`.
If `$rdi` is `1337` at that point, you get the flag!

Go and write a program that:

1. Moves `1337` into `rdi`
2. Executes `int3` to cooperatively hand control to the debugger

----
**NOTE:**
When an `int3` is executed by a program _not_ running under a debugger, you will see:

```
hacker@dojo:~$ /tmp/your-program
Trace/breakpoint trap
hacker@dojo:~$
```

And the program will terminate...
If you want the program to run outside a debugger, take out that `int3`!
