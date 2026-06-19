{% extends "base/base.c" %}

{% block includes %}
  {% include "embryogdb/auto_gdb.c" %}
{% endblock %}

{% block globals %}
  void __attribute__((always_inline)) breakpoint()
  {
    __asm__ volatile("int3");
  }
{% endblock +%}

{% block main %}

  {% filter layout_text %}
    GDB is a very powerful dynamic analysis tool which you can use in order to understand the state of a program throughout its execution.
    You will become familiar with some of gdb's capabilities in this module.
  {% endfilter %}

  {% include "embryogdb/lesson_{}.c".format(challenge.lesson) %}

  {% if challenge.info_breakpoint %}
    breakpoint();
  {% endif %}

  for (int i = 0; i < {{ challenge.challenge_iterations }}; i++) {
    uint64_t correct;
    uint64_t input;
    read(open("/dev/urandom", 0), &correct, sizeof(correct));

    {% if challenge.use_register %}
      asm("mov r12, %0" : : "r"(correct));
    {% endif %}

    {{ "The random value has been set!" | layout_text}}

    {% if challenge.prompt_breakpoint %}
      breakpoint();
    {% endif %}

    printf("Random value: ");
    scanf("%llx", &input);

    printf("You input: %llx\n", input);
    printf("The correct answer is: %llx\n", correct);

    if (input != correct)
      exit(1);
  }

  win();
{% endblock %}
