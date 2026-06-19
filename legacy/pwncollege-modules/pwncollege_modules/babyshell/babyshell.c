{% extends "base/base.c" %}

{% block includes %}
  {% include "disassemble.c" %}
{% endblock %}

{% block globals %}
  void *shellcode;
  size_t shellcode_size;
{% endblock %}

{% block main %}
  {% filter layout_text %}
    This challenge reads in some bytes, modifies them (depending on the specific challenge configuration), and executes them as code!
    This is a common exploitation scenario, called `code injection`.
    Through this series of challenges, you will practice your shellcode writing skills under various constraints!
    To ensure that you are shellcoding, rather than doing other tricks, this will sanitize all environment variables and arguments and close all file descriptors > 2.
  {% endfilter %}

  for (int i = 3; i < 10000; i++) close(i);
  for (char **a = argv; *a != NULL; a++) memset(*a, 0, strlen(*a));
  for (char **a = envp; *a != NULL; a++) memset(*a, 0, strlen(*a));

  {% if challenge.stack_shellcode %}
    {% include "babyshell/stack_shellcode.c" %}
  {% else %}
    {% include "babyshell/alloc_shellcode.c" %}
  {% endif %}


  {{ "Reading {} bytes from stdin.".format(hex(challenge.shellcode_size)) | layout_text }}
  shellcode_size = read(0, shellcode, {{ hex(challenge.shellcode_size) }});
  assert(shellcode_size > 0);

  {% if challenge.shellcode_filter %}
    {{ "Executing filter..." | layout_text }}
    {% include challenge.shellcode_filter %}
  {% endif +%}

  {% if challenge.remap_rx_size > 0 %}
    {{ "Removing write permissions from first {} bytes of shellcode.".format(challenge.remap_rx_size) | layout_text }}
    assert(mprotect(shellcode, {{ challenge.remap_rx_size }}, PROT_READ|PROT_EXEC) == 0);
  {% endif %}

  {{ "This challenge is about to execute the following shellcode:" | layout_text }}
  print_disassembly(shellcode, shellcode_size);
  {{ "" | layout_text }}

  {% if challenge.close_stdin %}
    {% filter layout_text %}
      This challenge is about to close stdin, which means that it will be harder to pass in a stage-2 shellcode.
      You will need to figure an alternate solution (such as unpacking shellcode in memory) to get past complex filters.
    {% endfilter %}
    assert(fclose(stdin) == 0);
  {% endif %}

  {% if challenge.close_stderr %}
    {% filter layout_text %}
      This challenge is about to close stderr, which means that you will not be able to use file descriptor 2 for output.
    {% endfilter %}
    assert(fclose(stderr) == 0);
  {% endif %}

  {% if challenge.close_stderr %}
    {% filter layout_text %}
      This challenge is about to close stdout, which means that you will not be able to use file descriptor 1 for output.
      You will see no further output, and will need to figure out an alternate way of communicating data back to yourself.
    {% endfilter %}
    assert(fclose(stdout) == 0);
  {% endif %}

  {{ "Executing shellcode!" | layout_text }}
  ((void(*)())shellcode)();
{% endblock %}
