{% filter layout_text %}
  As it turns out, gdb has FULL control over the target process.
  Not only can you analyze the program's state, but you can also modify it.
  While gdb probably isn't the best tool for doing long term maintenance on a program, sometimes it can be useful to quickly modify the behavior of your target process in order to more easily analyze it.
{% endfilter %}

{% filter layout_text %}
  You can modify the state of your target program with the `set` command.
  For example, you can use `set $rdi = 0` to zero out $rdi.
  You can use `set *((uint64_t *) $rsp) = 0x1234` to set the first value on the stack to 0x1234.
  You can use `set *((uint16_t *) 0x31337000) = 0x1337` to set 2 bytes at 0x31337000 to 0x1337.
{% endfilter %}

{% filter layout_text %}
  Suppose your target is some networked application which reads from some socket on fd 42.
  Maybe it would be easier for the purposes of your analysis if the target instead read from stdin.
  You could achieve something like that with the following gdb script:
{% endfilter %}

puts("  start");
puts("  catch syscall read");
puts("  commands");
puts("    silent");
puts("    if ($rdi == 42)");
puts("      set $rdi = 0");
puts("    end");
puts("    continue");
puts("  end");
puts("  continue");
puts("");

{% filter layout_text %}
  This example gdb script demonstrates how you can automatically break on system calls, and how you can use conditions within your commands to conditionally perform gdb commands.
{% endfilter %}

{% filter layout_text %}
  In the previous level, your gdb scripting solution likely still required you to copy and paste your solutions.
  This time, try to write a script that doesn't require you to ever talk to the program, and instead automatically solves each challenge by correctly modifying registers / memory.
{% endfilter %}
