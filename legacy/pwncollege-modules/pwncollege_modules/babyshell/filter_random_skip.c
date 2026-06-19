{% filter layout_text %}
  This challenge will randomly skip up to 0x800 bytes in your shellcode.
  You better adapt to that!
  One way to evade this is to have your shellcode start with a long set of single-byte instructions that do nothing, such as `nop`, before the actual functionality of your code begins.
  When control flow hits any of these instructions, they will all harmlessly execute and then your real shellcode will run.
  This concept is called a `nop sled`.
{% endfilter %}
srand(time(NULL));
int to_skip = (rand() % 0x700) + 0x100;
shellcode += to_skip;
shellcode_size -= to_skip;
