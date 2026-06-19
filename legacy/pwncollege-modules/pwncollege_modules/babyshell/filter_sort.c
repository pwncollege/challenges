{{ challenge.sort_type }} *input = shellcode;
int sort_max = shellcode_size / sizeof({{ challenge.sort_type }}) - 1;
for (int i = 0; i < sort_max; i++)
  for (int j = 0; j < sort_max-i-1; j++)
    if (input[j] > input[j+1]) {
      {{ challenge.sort_type }} x = input[j];
      {{ challenge.sort_type }} y = input[j+1];
      input[j] = y; input[j+1] = x;
    }
{% filter layout_text %}
  This challenge just sorted your shellcode using bubblesort.
  Keep in mind the impact of memory endianness on this sort (e.g., the LSB being the right-most byte).
{% endfilter %}
printf("This sort processed your shellcode %d bytes at a time.\n", sizeof({{ challenge.sort_type }}));
