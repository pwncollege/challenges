{% extends "base/base.c" %}

{% macro hex_print(data, length=challenge.input_size) -%}
  printf("\t");
  for (int i = 0; i < {{ length }}; i++)
    printf("%02x ", (unsigned char) {{ data }}[i]);
  printf("\n\n");
{%- endmacro %}

{% block includes %}
  {% if challenge.crackme %}
    #include <openssl/md5.h>
  {% endif %}
{% endblock %}

{% block globals %}
  char EXPECTED_RESULT[] = "{{ hex_str_repr(challenge.expected_result) }}";
{% endblock %}

{% block main %}
  {% filter layout_text %}
    This license verifier software will allow you to read the flag.
    However, before you can do so, you must verify that you are licensed to read flag files!
    This program consumes a license key over stdin.
    Each program may perform entirely different operations on that input!
    You must figure out (by reverse engineering this program) what that license key is.
    Providing the correct license key will net you the flag!
  {% endfilter %}

  {% if challenge.crackme %}
    {% filter layout_text %}
      Unfortunately for you, the license key cannot be reversed.
      You'll have to crack this program.
    {% endfilter %}

    unsigned short offset;
    unsigned char value;
    int page = 0;
    char *page_ptr = (((unsigned long long) bin_padding) & ~0xfff) - 0x1000;

    while (mprotect(page_ptr + 0x1000 * page++, 0x1000, PROT_READ|PROT_WRITE|PROT_EXEC) == 0);

    {% if challenge.crackme_integrity %}
      {{ "In order to ensure code integrity, the code will be hashed and verified." | layout_text }}
      unsigned char pre_hash[16];
      {
        MD5_CTX c;
        MD5_Init(&c);
        for (int i = 0; i < page - 1; i ++)
          MD5_Update(&c, page_ptr + 0x1000 * i, 0x1000);
        MD5_Final(pre_hash, &c);
      }
      {% if walkthrough %}
        {{ "The pre-crack code integrity hash is: " | layout_text }}
        {{ hex_print("pre_hash") }}
      {% endif %}
    {% endif %}

    for (int i = 0; i < {{ challenge.crackme_num_bytes }}; i++) {
      printf("Changing byte %d/{{ challenge.crackme_num_bytes }}.\n", i + 1);
      printf("Offset (hex) to change: ");
      scanf("%hx", &offset);
      printf("New value (hex): ");
      scanf("%hhx", &value);
      *(page_ptr + offset) = value;
      printf("The byte has been changed: *%p = %hhx.\n", (page_ptr + offset), value);
    }

    {% if challenge.crackme_integrity %}
      unsigned char post_hash[16];
      {
        MD5_CTX c;
        MD5_Init(&c);
        for (int i = 0; i < page - 1; i ++)
          MD5_Update(&c, page_ptr + 0x1000 * i, 0x1000);
        MD5_Final(post_hash, &c);
      }
      {% if walkthrough %}
        {{ "The post-crack code integrity hash is:" | layout_text }}
        {{ hex_print("post_hash") }}
      {% endif %}
      if (memcmp(pre_hash, post_hash, 16) == 0) {
        {{ "The code's integrity is secure!" | layout_text }}
      }
      else {
        {{ "The code's integrity has been breached, aborting!" | layout_text }}
        exit(1);
      }
    {% endif %}
  {% endif %}

  unsigned char input[{{ challenge.input_size + 1 }}] = { 0 };

  {{ "Ready to receive your license key!" | layout_text }}

  read(0, input, {{ challenge.input_size }});

  {% if walkthrough %}
    {{ "Initial input:" | layout_text }}
    {{ hex_print("input") }}
  {% endif %}

  {% for mangler, args in challenge.manglers %}
    {% include "babyrev/mangler_{}.c".format(mangler) %}

    {% if walkthrough %}
      {{ "This mangled your input, resulting in:" | layout_text }}
      {{ hex_print("input") }}
    {% endif %}
  {% endfor %}

  {% if walkthrough %}
    {% filter layout_text %}
      The mangling is done!
      The resulting bytes will be used for the final comparison.
    {% endfilter %}

    {{ "Final result of mangling input:" | layout_text }}
    {{ hex_print("input") }}

    {{ "Expected result:" | layout_text }}
    {{ hex_print("EXPECTED_RESULT") }}
  {% endif %}

  {{ "Checking the received license key!" | layout_text }}

  if (memcmp(input, EXPECTED_RESULT, {{ challenge.input_size }}) == 0) {
    win();
    exit(0);
  }
  else {
    puts("Wrong! No flag for you!");
    exit(1);
  }
{% endblock %}
