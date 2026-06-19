{% filter layout_text %}
  You can see the values for all your registers with `info registers`.
  Alternatively, you can also just print a particular register's value with the `print` command, or `p` for short.
  For example, `p $rdi` will print the value of $rdi in decimal.
  You can also print it's value in hex with `p/x $rdi`.
{% endfilter %}

{% filter layout_text %}
  In order to solve this level, you must figure out the current random value of register r12 in hex.
{% endfilter %}
