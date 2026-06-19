{% extends "base/base.c" %}

{% block includes %}
  #include <openssl/evp.h>

  {% if walkthrough %}
    {% include "stack_recon.c" %}

    {% if not win_function %}
      {% include "disassemble.c" %}
    {% endif %}
  {% endif %}
{% endblock %}

{% block globals %}
  EVP_CIPHER_CTX *ctx;
{% endblock %}

{% block challenge_function %}
  unsigned char key[16];
  struct {
    char header[8];
    unsigned long long length;
    char message[{{challenge.message_buffer_length}}];
  } plaintext = {0};

  // initialize the cipher
  int key_file = open("/challenge/.key", O_RDONLY);
  assert(key_file);
  assert(read(key_file, key, 16) == 16);
  ctx = EVP_CIPHER_CTX_new();
  EVP_DecryptInit_ex(ctx, EVP_aes_128_ecb(), NULL, key, NULL);
  close(key_file);

  char *ciphertext = malloc(0x1000);
  size_t ciphertext_len = read(0, ciphertext, 0x1000);
  assert(ciphertext_len % 16 == 0);  // should be padded
  assert(ciphertext_len >= 16);      // at least one block

  // first, we verify the first block
  int decrypted_len;
  EVP_CIPHER_CTX_set_padding(ctx, 0);  // disable padding for the first block
  EVP_DecryptUpdate(ctx, (char *)&plaintext, &decrypted_len, ciphertext, 16);

  {% if walkthrough %}
    fprintf(stderr, "Your message header: %8s\n", plaintext.header);
    fprintf(stderr, "Your message length: %llu\n", plaintext.length);
  {% endif %}
  assert(memcmp(plaintext.header, "VERIFIED", 8) == 0); // verify header
  assert(plaintext.length <= 16); // verify length

  // decrypt the message!
  ctx = EVP_CIPHER_CTX_new();
  EVP_DecryptInit_ex(ctx, EVP_aes_128_ecb(), NULL, key, NULL);
  memset(key, 0, sizeof(key));
  EVP_DecryptUpdate(ctx, plaintext.message, &decrypted_len, ciphertext + 16, ciphertext_len - 16);
  EVP_DecryptFinal_ex(ctx, plaintext.message + decrypted_len, &decrypted_len);

  printf("Decrypted message: %s!\n", plaintext.message);

  {% if walkthrough %}
    {% if not challenge.win_function %}
      fprintf(stderr, "You've loaded the following shellcode into your message:\n");
      print_disassembly(plaintext.message, decrypted_len);
      fprintf(stderr, "\n");
    {% endif %}

    GET_FRAME_WORDS(sz_, sp_, bp_, rp_);
    DUMP_STACK(sp_, sz_);
    fprintf(stderr, "The program's memory status:\n");
    fprintf(stderr, "- the input buffer starts at %p\n", plaintext.message);
    fprintf(stderr, "- the saved return address (previously to main) is at %p\n", rp_);
    {% if challenge.win_function %}
      fprintf(stderr, "- the address of win() is %p.\n", win);
    {% endif %}

  {% endif%}
{% endblock %}
