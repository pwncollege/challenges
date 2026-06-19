{% filter layout_text %}
  In this challenge, shellcode will be copied onto the stack and executed.
  Since the stack location is randomized on every execution, your shellcode will need to be *position-independent*.
{% endfilter %}

uint8_t shellcode_buffer[{{ hex(challenge.allocation_size) }}];
shellcode = (void *)&shellcode_buffer;
printf("Allocated {{ hex(challenge.allocation_size) }} bytes for shellcode on the stack at %p!\n", shellcode);
