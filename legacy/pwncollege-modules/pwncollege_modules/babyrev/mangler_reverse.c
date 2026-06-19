{% filter layout_text_walkthrough %}
  This challenge is now mangling your input using the `reverse` mangler.
{% endfilter %}

for (int i = 0; i < {{ challenge.input_size }} / 2; i++) {
  unsigned char x = input[i];
  unsigned char y = input[{{ challenge.input_size }} - i - 1];
  input[i] = y;
  input[{{ challenge.input_size }} - i - 1] = x;
}
