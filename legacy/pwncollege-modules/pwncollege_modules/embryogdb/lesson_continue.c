{% filter layout_text %}
  You are running in gdb!
  The program is currently paused.
  This is because it has set its own breakpoint here.
{% endfilter %}

{% filter layout_text %}
  You can use the command `start` to start a program, with a breakpoint set on `main`.
  You can use the command `starti` to start a program, with a breakpoint set on `_start`.
  You can use the command `run` to start a program, with no breakpoint set.
  You can use the command `attach <PID>` to attach to some other already running program.
  You can use the command `core <PATH>` to analyze the coredump of an already run program.
{% endfilter %}

{% filter layout_text %}
  When starting or running a program, you can specify arguments in almost exactly the same way as you would on your shell.
  For example, you can use `start <ARGV1> <ARGV2> <ARGVN> < <STDIN_PATH>`.
{% endfilter %}

{% filter layout_text %}
  Use the command `continue`, or `c` for short, in order to continue program execution.
{% endfilter %}
