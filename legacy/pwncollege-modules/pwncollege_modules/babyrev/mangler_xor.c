{% if walkthrough %}
  {% filter layout_text %}
    This challenge is now mangling your input using the `xor` mangler with key `{{ HEX_LIST(args[0]) }}`
  {% endfilter %}
{% endif %}

for (int i = 0; i < {{ challenge.input_size }}; i++) {
  switch(i % {{ args[0] | length }}) {
  {% for key_i in args[0] %}
  case {{ loop.index0 }}:
    input[i] ^= {{ hex(key_i) }};
    break;
  {% endfor %}
  }
}
