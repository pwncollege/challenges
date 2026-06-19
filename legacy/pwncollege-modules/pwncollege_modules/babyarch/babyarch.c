{% extends "base/base.c" %}

{% block includes %}
  {% if challenge.syscalls_allowed %}
    #include <seccomp.h>
  {% endif %}

  {% if challenge.shellcode %}
    {% include "disassemble.c" %}
  {% endif %}

{% endblock +%}

{% block main %}
  {% if challenge.shellcode %}
    {{ "You may upload custom shellcode to do whatever you want." | layout_text }}
  {% endif %}

  {% if challenge.prefetch %}
    {{ "For extra security, this challenge will only allow the exit system call!" | layout_text }}

    // using 3 bytes of random, need to see if that is enough
    int rand_bytes = 3;

    // bounds of our flag page [0x10000, 0xffffff0000)
    int lower_shift = 16;
    int upper_shift = lower_shift + (rand_bytes*8);

    uint64_t rand = 0;

    int rand_fd = open("/dev/urandom", O_RDONLY);
    read(rand_fd, &rand, rand_bytes);
    close(rand_fd);

    rand = rand << lower_shift;

    uint64_t *flag_page = mmap(rand, 0x1000, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANON|MAP_FIXED, 0, 0);
    assert(flag_page >= (1ull<<lower_shift) && flag_page < (1ull<<upper_shift));

    int flag_fd = open("/flag", O_RDONLY);
    assert(flag_fd == 3);

    read(flag_fd, flag_page, 0x40);

    close(flag_fd);

    // kill the reference to the page, might need to clear regs still
    flag_page = 0;
    rand = 0;
  {% endif %}

  {% if challenge.shellcode %}
    void *shellcode = mmap((void *)0x13333370000, 0x1000, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_PRIVATE|MAP_ANON, 0, 0);
    assert(shellcode == (void *)0x13333370000);
    printf("Mapped 0x1000 bytes for shellcode at %p!\n", shellcode);

    {{ "Reading 0x1000 bytes of shellcode from stdin." | layout_text }}
    int shellcode_size = read(0, shellcode, 0x1000);

    {{ "This challenge is about to execute the following shellcode:" | layout_text }}
    print_disassembly(shellcode, shellcode_size);
    {{ "" | layout_text }}

    {% include "babyarch/seccomp_init.c" %}

    {{ "Executing shellcode!" | layout_text }}

    {% if challenge.syscalls_allowed %}
    assert(seccomp_load(ctx) == 0);
    {% endif %}

    ((void(*)())shellcode)();
  {% endif %}

{% endblock %}
