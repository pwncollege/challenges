{% filter layout_text %}
  This challenge requires that your shellcode have no H bytes!
{% endfilter %}
for (int i = 0; i < shellcode_size; i++)
  if (((uint8_t *)shellcode)[i] == 'H') {
    printf("Failed filter at byte %d!\n", i);
    exit(1);
  }
