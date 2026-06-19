for (int i = 0; i < shellcode_size; i++) {
  if ((i / 10) % 2 == 1) {
    ((unsigned char *)shellcode)[i] = '\xcc';
  }
}
{% filter layout_text %}
  This challenge modified your shellcode by overwriting every other 10 bytes with 0xcc.
  0xcc, when interpreted as an instruction is an `INT 3`, which is an interrupt to call into the debugger.
  You must avoid these modifications in your shellcode.
{% endfilter %}
