{% filter layout_text %}
  This challenge requires that your shellcode does not have any `syscall`, 'sysenter', or `int` instructions.
  System calls are too dangerous!
  This filter works by scanning through the shellcode for the following byte sequences: 0f05 (`syscall`), 0f34 (`sysenter`), and 80cd (`int`).
  One way to evade this is to have your shellcode modify itself to insert the `syscall` instructions at runtime.
{% endfilter %}
for (int i = 0; i < shellcode_size; i++) {
  uint16_t *scw = (uint16_t *)((uint8_t *)shellcode + i);
  if (*scw == 0x80cd || *scw == 0x340f || *scw == 0x050f) {
    printf("Failed filter at byte %d!\n", i);
    exit(1);
  }
}
