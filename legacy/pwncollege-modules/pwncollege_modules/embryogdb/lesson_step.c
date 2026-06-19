{% filter layout_text %}
  A critical part of dynamic analysis is getting your program to the state you are interested in analyzing.
  So far, these challenges have automatically set breakpoints for you to pause execution at states you may be interested in analyzing.
  It is important to be able to do this yourself.
{% endfilter %}

{% filter layout_text %}
  There are a number of ways to move forward in the program's execution.
  You can use the `stepi <n>` command, or `si <n>` for short, in order to step forward one instruction.
  You can use the `nexti <n>` command, or `ni <n>` for short, in order to step forward one instruction, while stepping over any function calls.
  The `<n>` parameter is optional, but allows you to perform multiple steps at once.
  You can use the `finish` command in order to finish the currently executing function.
  You can use the `break *<address>` parameterized command in order to set a breakpoint at the specified-address.
  You have already used the `continue` command, which will continue execution until the program hits a breakpoint.
{% endfilter %}

{% filter layout_text %}
  While stepping through a program, you may find it useful to have some values displayed to you at all times.
  There are multiple ways to do this.
  The simplest way is to use the `display/<n><u><f>` parameterized command, which follows exactly the same format as the `x/<n><u><f>` parameterized command.
  For example, `display/8i $rip` will always show you the next 8 instructions.
  On the other hand, `display/4gx $rsp` will always show you the first 4 values on the stack.
  Another option is to use the `layout regs` command.
  This will put gdb into its TUI mode and show you the contents of all of the registers, as well as nearby instructions.
{% endfilter %}

{% filter layout_text %}
  In order to solve this level, you must figure out a series of random values which will be placed on the stack.
  You are highly encouraged to try using combinations of `stepi`, `nexti`, `break`, `continue`, and `finish` to make sure you have a good internal understanding of these commands.
  The commands are all absolutely critical to navigating a program's execution.
{% endfilter %}
