__attribute__((constructor))
void init(void)
{
	// disable buffering
	setbuf(stdin, NULL);
	setbuf(stdout, NULL);
	setbuf(stderr, NULL);
}

{% if challenge.bss_read %}
  struct {
    char asdf[ {{ challenge.bss_padding }} ];
    char flag[128];
  } global;
{% endif %}

{% if challenge.bss_write or challenge.copy_val %}
  struct {
    char asdf[{{ challenge.bss_padding }}];
    unsigned long win_value;
  } global;
{% endif %}


struct stack_frame {
  char random_data[{{ challenge.random_data_length }}];
  char *password;
  char *not_used_spacer;
  char answer[16];
  int i;
  int num_bytes;
  char asdf[{{ challenge.fmt_padding }}];
  char format_string[{{ challenge.fmtstr_bytes }} + 1];
  char fdsa[{{ challenge.fmt_padding }}];
  unsigned long required_win_value;
};



{% if challenge.win_func %}
void win(void) {
	puts("You win! Here is your flag:");
	sendfile(1, open("/flag", 0), 0, 0x400);
	exit(0);
}
{% endif %}


{% if challenge.check_win_func %}
void check_win(unsigned long win_value) {
  printf("Checking win value...\n");
  {% if challenge.bss_write %}
    printf("... desired win value: %#lx\n", (unsigned long) {{ challenge.win_value }});
  {% endif %}

  {% if challenge.copy_val %}
    printf("... desired win value: %#lx\n", (unsigned long)  win_value);
  {% endif %}

  printf("... written win value: %#lx\n", global.win_value);

  {% if challenge.bss_write %}
    if (global.win_value == {{ challenge.win_value }})
  {% else %}
    if (global.win_value == win_value)
  {% endif %}
  {
    printf("... SUCCESS! Here is your flag:\n");
    sendfile(1, open("/flag", 0), 0, 128);
  }
  else
  {
    printf("... INCORRECT!\n");
  }
}
{% endif %}
