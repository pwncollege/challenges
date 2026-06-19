{% extends "base/base.c" %}

{% block includes %}
  {% if challenge.syscalls_allowed %}
    #include <seccomp.h>
  {% endif %}
{% endblock %}

{% block globals %}
  struct ypu {
    int fd;
    void *code;
  };

  struct {
    {% if not challenge.local_programs %}
      unsigned char programs[16][3 * 256];
    {% endif %}
    {% if challenge.atomic_ypu %}
      sem_t ypu_mutexes[16];
    {% endif %}
    struct ypu ypus[16];
  } data;
  {% if not challenge.local_programs %}
    #define programs data.programs
  {% endif %}
  #define ypus data.ypus
  {% if challenge.atomic_ypu %}
    #define ypu_mutexes data.ypu_mutexes
  {% endif %}
{% endblock %}

{% block initialize_server %}
  for (int i = 0; i < 16; i++) {
    {% if challenge.atomic_ypu %}
      sem_init(&ypu_mutexes[i], 0, 1);
    {% endif %}

    int fd = open("/proc/ypu", O_RDWR);
    ypus[i].fd = fd;
    ypus[i].code = mmap(0, 0x1000, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
  }

  {% include "babyjail/seccomp_init.c" %}

  assert(seccomp_load(ctx) == 0);
{% endblock %}

{% block challenge_function %}
  printf("Welcome to the YPU (yan85 processing unit) server!\n");
  printf("This server will allow you to schedule yan85 computing tasks onto dedicated YPUs.\n");
  printf("Commands: load_program/init_ypu/run_ypu/quit.\n");

  {% if challenge.local_programs %}
    unsigned char programs[16][3 * 256];
  {% endif %}

  while (true) {
    char command[16] = { 0 };
    unsigned int program_index;
    unsigned int ypu_index;

    scanf("%15s", command);

    if (!strcmp(command, "load_program")) {
      scanf("%d", &program_index);
      assert(program_index < 16);
      read({{ "fileno(thread_stdin)" if challenge.threaded_server else "0" }},
           programs[program_index],
           0x1000);
    }

    else if (!strcmp(command, "init_ypu")) {
      scanf("%d", &ypu_index);
      assert(ypu_index < 16);
      scanf("%d", &program_index);
      assert(program_index < 16);
      {% if challenge.atomic_ypu %}
        sem_wait(&ypu_mutexes[ypu_index]);
      {% endif %}
      memcpy(ypus[ypu_index].code, programs[program_index], 0x1000);
      {% if challenge.atomic_ypu %}
        sem_post(&ypu_mutexes[ypu_index]);
      {% endif %}
    }

    else if (!strcmp(command, "run_ypu")) {
      scanf("%d", &ypu_index);
      assert(ypu_index < 16);
      {% if challenge.atomic_ypu %}
        sem_wait(&ypu_mutexes[ypu_index]);
      {% endif %}
      ioctl(ypus[ypu_index].fd, 1337, NULL);
      {% if challenge.atomic_ypu %}
        sem_post(&ypu_mutexes[ypu_index]);
      {% endif %}
    }

    else if (!strcmp(command, "quit")) {
      break;
    }

    else {
      printf("Unrecognized choice!\n");
    }
  }
{% endblock %}
