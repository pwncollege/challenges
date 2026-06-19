{% if walkthrough %}
  {% filter layout_text %}
    This challenge is now mangling your input using the `sort` mangler.
  {% endfilter %}
{% endif %}

for (int i = 0; i < {{ challenge.input_size }} - 1; i++) {
  for (int j = 0; j < {{ challenge.input_size }} - i - 1; j++) {
    if (input[j] > input[j + 1]) {
      unsigned char x = input[j];
      unsigned char y = input[j + 1];
      input[j] = y;
      input[j + 1] = x;
    }
  }
}
