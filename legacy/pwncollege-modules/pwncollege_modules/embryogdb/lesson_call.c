{% filter layout_text %}
  As we demonstrated in the previous level, gdb has FULL control over the target process.
  Under normal circumstances, gdb running as your regular user cannot attach to a privileged process.
  This is why gdb isn't a massive security issue which would allow you to just immediately solve all the levels.
  Nevertheless, gdb is still an extremely powerful tool.
{% endfilter %}

{% filter layout_text %}
  Running within this elevated instance of gdb gives you elevated control over the entire system.
  To clearly demonstrate this, see what happens when you run the command `call (void)win()`.
{% endfilter %}

{% if challenge.win_function_broken %}
{% filter layout_text %}
  Note that this will _not_ get you the flag (it seems that we broke the win function!), so you'll need to work a bit harder to get this flag!
{% endfilter %}
{% endif %}

{% filter layout_text %}
As it turns out, all of the levels other levels in module could be solved in this way.
{% endfilter %}

{% filter layout_text %}
  GDB is very powerful!
{% endfilter %}

breakpoint();

exit(42);
