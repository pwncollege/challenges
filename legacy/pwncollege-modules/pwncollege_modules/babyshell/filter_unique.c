{% filter layout_text %}
  This challenge requires that every byte in your shellcode is unique!
{% endfilter %}
unsigned char present[256] = {0};
for (int i = 0; i < shellcode_size; i++) {
  if (present[((uint8_t *)shellcode)[i]]) {
    printf("Failed filter at byte %d!\n", i);
    exit(1);
  }
  present[((uint8_t *)shellcode)[i]] = 1;
}
