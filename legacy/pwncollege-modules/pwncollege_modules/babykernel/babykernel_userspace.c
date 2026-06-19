{% extends "base/base.c" %}

{% block includes %}
  {% if challenge.syscalls_allowed %}
    #include <seccomp.h>
  {% endif %}

  {% if challenge.load_flag_hang %}
    #include <semaphore.h>
  {% endif %}

  {% if challenge.shellcode %}
    {% include "disassemble.c" %}
  {% endif %}
{% endblock +%}

{% block globals %}
  {% if challenge.load_flag %}
    void load_flag()
    {
      {{ "Attempting to load the flag into memory." | layout_text }}

      {% if challenge.load_flag_hang %}
        sem_t *sem = mmap(0, 0x1000, PROT_READ|PROT_WRITE, MAP_SHARED|MAP_ANON, 0, 0);
        sem_init(sem, 1, 0);
      {% endif %}

      if (!fork()) {
        static char flag[256];

        int flag_fd = open("/flag", 0);
        if (flag_fd < 0)
          exit(1);

        read(flag_fd, flag, sizeof(flag));
        close(flag_fd);

        {% if challenge.load_flag_hang %}
          sem_post(sem);
          while (true)
            sleep(1);
        {% endif %}

        exit(0);
      }
      else {
        {% if challenge.load_flag_hang %}
          sem_wait(sem);
        {% else %}
          wait(0);
        {% endif %}
      }
    }
  {% endif %}
{% endblock %}

{% block main %}
  {% if challenge.shellcode %}
    {{ "You may upload custom shellcode to do whatever you want." | layout_text }}
  {% endif %}

  {% if challenge.syscalls_allowed %}
    {{ "For extra security, this challenge will only allow certain system calls!" | layout_text }}
  {% endif %}

  {% if challenge.load_flag %}
    load_flag();
  {% endif %}

  {% if challenge.delete_flag %}
    unlink("/flag");
    {{ "The flag has been deleted!" | layout_text }}
  {% endif %}

  {% if challenge.open_device %}
    int device_fd = open("{{ challenge.device_path }}", O_RDWR);
    printf("Opened `{{ challenge.device_path }}` on fd %d.\n", device_fd);
    {{ "" | layout_text }}
  {% endif %}

  {% if challenge.shellcode %}
    void *shellcode = mmap((void *)0x31337000, 0x1000, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_PRIVATE|MAP_ANON, 0, 0);
    assert(shellcode == (void *)0x31337000);
    printf("Mapped 0x1000 bytes for shellcode at %p!\n", shellcode);

    {{ "Reading 0x1000 bytes of shellcode from stdin." | layout_text }}
    int shellcode_size = read(0, shellcode, 0x1000);

    {{ "This challenge is about to execute the following shellcode:" | layout_text }}
    print_disassembly(shellcode, shellcode_size);
    {{ "" | layout_text }}

    {% include "babyjail/seccomp_init.c" %}

    {{ "Executing shellcode!" | layout_text }}

    {% if challenge.syscalls_allowed %}
    assert(seccomp_load(ctx) == 0);
    {% endif %}

    ((void(*)())shellcode)();
  {% endif %}
{% endblock %}
