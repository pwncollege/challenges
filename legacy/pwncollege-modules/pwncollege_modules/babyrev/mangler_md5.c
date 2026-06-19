{% filter layout_text_walkthrough %}
  This challenge is now mangling your input using the `md5` mangler.
  This mangler cannot be reversed.
{% endfilter %}

{
  MD5_CTX c;
  unsigned char digest[16];
  MD5_Init(&c);
  MD5_Update(&c, input, {{ challenge.input_size }});
  MD5_Final(digest, &c);
  memset(input, 0, {{ challenge.input_size }});
  memcpy(input, digest, {{ min(challenge.input_size, 16) }});
}
