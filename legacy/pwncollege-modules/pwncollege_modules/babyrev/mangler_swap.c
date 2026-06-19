{% if walkthrough %}
  {% filter layout_text %}
    This challenge is now mangling your input using the `swap` mangler for indexes `{{ args[0] }}` and `{{ args[1] }}`.
  {% endfilter %}
{% endif %}

{
  unsigned char x = input[{{ args[0] }}];
  unsigned char y = input[{{ args[1] }}];
  input[{{ args[0] }}] = y;
  input[{{ args[1] }}] = x;
}
