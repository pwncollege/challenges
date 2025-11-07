Debuggers, including gdb, observe the debugged program _as it runs_ to expose information about its runtime behavior.
In the previous level, we automatically launched the program for you.
Here, we will tone down the magic somewhat: you must start the execution of the program, and we'll do the rest (e.g., recover the secret value from it).

When you launch gdb now, it will eventually bring up a command prompt, that looks like this:

```gdb
(gdb) 
```

You start a program with the `starti` command:

```gdb
(gdb) starti
```

`starti` **start**s the program at the very first **i**nstruction.
Give it a try now, and we'll configure gdb to magically extract the secret value once the program is running.
