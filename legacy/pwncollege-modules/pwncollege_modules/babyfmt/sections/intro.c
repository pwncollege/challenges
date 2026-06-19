// challenge introduction

{% if challenge.intro_chal %}
  printf("This challenge reads in some bytes, calls printf on that string, and allows you to perform\n");
  printf("a format string attack. Through this series of challenges, you will become painfully familiar\n");
  printf("with the concept of Format String Attacks!\n");
  printf("\n");

  printf("This challenge allows you to make a %d-sized format string.\n",{{ challenge.fmtstr_bytes }});
  printf("\n");
{% else %}
  printf("In this challenge, you will be performing attack against the old and famous vulnerability:\n"
		"\"format string vulnerability\". This challenge reads in some bytes and print the\n"
		"input as the format using `printf` in different ways(depending on the specific challenge\n"
		"configuration). Different challenges have different protections on. ROP may be needed in\n"
		"some challenges. Have fun!\n");
{% endif %}
