Next, let's move on to GDB.
GDB stands for the **G**NU **D**e**b**ugger, and it is typically used to hunt down and understand bugs.
More specifically, a debugger is a tool that enables the close monitoring and introspection of another process.
There are many famous debuggers, and in the Linux space, gdb is by far the most common.

We'll learn gdb step by step through a series of challenges.
In this one, we'll focus on simply launching it.
That's done as so:

```console
hacker@dojo:~$ gdb /path/to/binary/file
```

In this challenge, the binary that holds the secret is `/challenge/debug-me`.
Once you load it in gdb, the rest will happen magically: we'll handle the analysis and give you the secret number.
In later levels, you'll learn how to get that number on your own!

Again, once you have the number, exchange it for the flag with `/challenge/submit-number`.
