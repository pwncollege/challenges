{% filter layout_text %}
  We write code in order to express an idea which can be reproduced and refined.
  We can think of our analysis as a program which injests the target to be analyzed as data.
  As the saying goes, code is data and data is code.
{% endfilter %}

{% filter layout_text %}
  While using gdb interactively as we've done with the past levels is incredibly powerful, another powerful tool is gdb scripting.
  By scripting gdb, you can very quickly create a custom-tailored program analysis tool.
  If you know how to interact with gdb, you already know how to write a gdb script--the syntax is exactly the same.
  You can write your commands to some file, for example `x.gdb`, and then launch gdb using the flag `-x <PATH_TO_SCRIPT>`.
  This file will execute all of the gdb commands after gdb launches.
  Alternatively, you can execute individual commands with `-ex '<COMMAND>'`.
  You can pass multiple commands with multiple `-ex` arguments.
  Finally, you can have some commands be always executed for any gdb session by putting them in `~/.gdbinit`.
  You probably want to put `set disassembly-flavor intel` in there.
{% endfilter %}

{% filter layout_text %}
  Within gdb scripting, a very powerful construct is breakpoint commands.
  Consider the following gdb script:
{% endfilter %}

puts("  start");
puts("  break *main+42");
puts("  commands");
puts("    x/gx $rbp-0x32");
puts("    continue");
puts("  end");
puts("  continue");
puts("");

{% filter layout_text %}
  In this case, whenever we hit the instruction at `main+42`, we will output a particular local variable and then continue execution.
{% endfilter %}

{% filter layout_text %}
  Now consider a similar, but slightly more advanced script using some commands you haven't yet seen:
{% endfilter %}

puts("  start");
puts("  break *main+42");
puts("  commands");
puts("    silent");
puts("    set $local_variable = *(unsigned long long*)($rbp-0x32)");
puts("    printf \"Current value: %llx\\n\", $local_variable");
puts("    continue");
puts("  end");
puts("  continue");
puts("");

{% filter layout_text %}
  In this case, the `silent` indicates that we want gdb to not report that we have hit a breakpoint, to make the output a bit cleaner.
  Then we use the `set` command to define a variable within our gdb session, whose value is our local variable.
  Finally, we output the current value using a formatted string.
{% endfilter %}

{% filter layout_text %}
  Use gdb scripting to help you collect the random values.
{% endfilter %}
