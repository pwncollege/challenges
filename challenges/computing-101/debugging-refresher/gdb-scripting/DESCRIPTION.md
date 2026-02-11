We write code in order to express an idea which can be reproduced and refined.
We can think of our analysis as a program which injests the target to be analyzed as data.
As the saying goes, code is data and data is code.

While using gdb interactively as we've done with the past levels is incredibly powerful, another powerful tool is gdb scripting.
By scripting gdb, you can very quickly create a custom-tailored program analysis tool.
If you know how to interact with gdb, you already know how to write a gdb script--the syntax is exactly the same.
You can write your commands to some file, for example `x.gdb`, and then launch gdb using the flag `-x <PATH_TO_SCRIPT>`.
This file will execute all of the gdb commands after gdb launches.
Alternatively, you can execute individual commands with `-ex '<COMMAND>'`.
You can pass multiple commands with multiple `-ex` arguments.
Finally, you can have some commands be always executed for any gdb session by putting them in `~/.gdbinit`.
You probably want to put `set disassembly-flavor intel` in there.

Within gdb scripting, a very powerful construct is breakpoint commands. Consider the following gdb script:

```gdb
start
break *main+42
commands
  x/gx $rbp-0x32
  continue
end
continue
```

In this case, whenever we hit the instruction at `main+42`, we will output a particular local variable and then continue execution.

Now consider a similar, but slightly more advanced script using some commands you haven't yet seen:

```gdb
start
break *main+42
commands
  silent
  set $local_variable = *(unsigned long long*)($rbp-0x32)
  printf "Current value: %llx\n", $local_variable
  continue
end
continue
```

In this case, the `silent` indicates that we want gdb to not report that we have hit a breakpoint, to make the output a bit cleaner.
Then we use the `set` command to define a variable within our gdb session, whose value is our local variable.
Finally, we output the current value using a formatted string.

Use gdb scripting to help you collect the random values in this level.
This may feel difficult, but will serve you well in your journey ahead.

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
- gdb's [breakpoint scripting](https://sourceware.org/gdb/current/onlinedocs/gdb#Break-Commands)
