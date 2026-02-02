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
Once the program is running, you can use other gdb commands to inspect its actual runtime state.
We'll start with the code that's running, which you can disassemble using the `disassemble` command!
For example:

```gdb
(gdb) disassemble
Dump of assembler code for function main:
=> 0x0000000000401000 <+0>:     mov    rdi,0x539
   0x0000000000401007 <+7>:     mov    rdi,0x0
   0x000000000040100e <+14>:    mov    rax,0x3c
   0x0000000000401015 <+21>:    syscall
End of assembler dump.
```

This is the same program from the objdump challenge, now running in gdb.
Like before, you can gleam its secrets by reading the disassembly, though later we'll dig even deeper!
For now, run `starti` after loading the binary in gdb, and we'll take care of the rest.
