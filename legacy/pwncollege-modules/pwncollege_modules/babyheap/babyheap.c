{% extends "base/base.c" %}

{% block includes %}
  {% if challenge.flag_seed %}
    {% include "flag_seed.c" %}
  {% endif %}

  {% if walkthrough %}
    {% include "heap_recon.c" %}
  {% endif %}
{% endblock %}

{% block globals %}
  {% if challenge.secret_size and not challenge.stack_buffer %}
    struct {
      char padding[{{ challenge.secret_padding}}];
      char secret[{{ challenge.secret_size }}];
    } __attribute__ ((aligned (1 << 16), packed)) secret;
  {% endif %}

  {% if "echo" in challenge.functions %}
    const char bin_echo[] = "/bin/echo";
    {% if not challenge.stack_data_prefix %}
      const char data_prefix[] = "Data:";
    {% endif %}
    void echo(char *data, size_t offset)
    {
      {% if challenge.stack_data_prefix %}
        char data_prefix[] = "Data:";
      {% endif %}

      char **execve_struct = malloc(sizeof(char *) * 4);
      execve_struct[0] = bin_echo;
      execve_struct[1] = data_prefix;
      execve_struct[2] = data + offset;
      execve_struct[3] = NULL;

      if (fork()) {
        wait(0);
      }
      else {
        execve(execve_struct[0], execve_struct, NULL);
        exit(0);
      }
    }
  {% endif %}
{% endblock %}

{% block main %}
  char response[128];

  {% if challenge.stack_buffer and challenge.secret_size %}
    struct {
      char stack_buffer[128];
      char secret_padding[{{ challenge.secret_padding }}];
      char secret[{{ challenge.secret_size }}];
    } secret;
    {% set stack_buffer = "secret.stack_buffer" %}

  {% elif challenge.stack_buffer %}
    char stack_buffer[128];
    {% set stack_buffer = "stack_buffer" %}
  {% endif %}

  char *allocations[{{ challenge.num_allocations }}] = { 0 };
  {% if "safe_write" in challenge.functions %}
  FILE *stdout_file = NULL;
  unsigned long allocations_size[{{ challenge.num_allocations }}] = { 0 };
  {% endif %}
  unsigned int allocation_index;
  unsigned int size;
  unsigned int offset;

  {% if challenge.num_mallocs %}
    int num_mallocs = 0;
  {% endif %}

  {% if challenge.randomize_stack_padding %}
    char magic_padding[{{ challenge.stack_padding }}];
  {% endif %}

  {% if challenge.runtime_flag_buffer_size %}
    char *flag_buffer;
    size_t flag_buffer_size = (rand() % (1000 - 128)) + 128;

  {% elif "puts_flag" in challenge.functions %}
    typedef struct {
      unsigned long long can_puts;
      unsigned long long padding;
      char data[{{ challenge.flag_buffer_size }}];
    } flag_buffer_t;
    flag_buffer_t *flag_buffer;
    size_t flag_buffer_size = sizeof(flag_buffer_t);

  {% else %}
    char *flag_buffer;
    size_t flag_buffer_size = {{ challenge.flag_buffer_size }};
  {% endif %}

  {% if challenge.secret_size %}
    for (int i = 0; i < {{ challenge.secret_size }}; i++)
      secret.secret[i] = (rand() % ('z' - 'a' + 1)) + 'a';
  {% endif %}

  {% if walkthrough %}
    {% filter layout_text_walkthrough %}
      This challenge allows you to perform various heap operations, some of which may involve the flag.
      Through this series of challenges, you will become familiar with the concept of heap exploitation.
    {% endfilter %}

    printf("This challenge can manage up to %d unique allocations.\n\n", {{ challenge.num_allocations }});

    {% if challenge.runtime_flag_size %}
      {% filter layout_text_walkthrough %}
        In this challenge, the size allocated for the flag buffer is not hardcoded.
        It is is derived from the flag.
      {% endfilter %}
    {% endif %}

    {% if challenge.num_flag_buffer_allocs > 1 %}
      printf("In this challenge, the flag buffer is allocated %d times before it is used.\n\n", {{ challenge.num_flag_buffer_allocs }});
    {% endif %}

    {% if challenge.secret_size %}
      printf("In this challenge, there is a secret stored at %p.\n", secret.secret);
      {% if challenge.whitespace_armor %}
        {{ "This address intentionally uses `whitespace-armoring` (notice the 0x0a in the address)." | layout_text_walkthrough }}
      {% elif challenge.discard_secret_malloc %}
        {{ "If you attempt to malloc an address near where the secret is stored, it will be discarded." | layout_text_walkthrough }}
      {% else %}
        {{ "If you can leak out this secret, you can redeem it for the flag." | layout_text_walkthrough }}
      {% endif %}
    {% endif %}
  {% endif %}

  {% if challenge.leak_stack_allocations %}
    printf("[LEAK] The local stack address of your allocations is at: %p.\n\n", allocations);
  {% endif %}

  {% if challenge.leak_pie_main %}
    printf("[LEAK] The address of main is at: %p.\n\n", main);
  {% endif %}

  while (true) {
    {% if walkthrough %}
      print_tcache(main_thread_tcache);
    {% endif %}

    puts("");
    printf("[*] Function ({{ challenge.functions_description }}): ");
    scanf("%127s", response);
    puts("");

    if (!strcmp(response, "malloc")) {
      {% if challenge.num_mallocs %}
        if (num_mallocs >= {{ challenge.num_mallocs }}) {
          printf("You are only allowed to trigger one malloc!");
          continue;
        }
        num_mallocs++;
      {% endif %}
      {% if challenge.num_allocations > 1 %}
        printf("Index: ");
        scanf("%127s", response);
        puts("");
        allocation_index = atoi(response);
        assert(allocation_index < {{ challenge.num_allocations }});
      {% else %}
        allocation_index = 0;
      {% endif %}

      printf("Size: ");
      scanf("%127s", response);
      puts("");
      size = atoi(response);

      {% if walkthrough %}
        printf("[*] allocations[%d] = malloc(%d)\n", allocation_index, size);
      {% endif %}
      allocations[allocation_index] = malloc(size);

      {% if "safe_write" in challenge.functions %}
        allocations_size[allocation_index] = size + 16;
      {% endif %}

      {% if challenge.discard_secret_malloc %}
        if ((unsigned long long) allocations[allocation_index] < (unsigned long long) &secret + sizeof(secret)) {
          printf("Invalid allocation detected: discarded!\n");
          allocations[allocation_index] = NULL;
          continue;
        }
      {% endif %}
      {% if walkthrough or challenge.print_malloc_pointers %}
        printf("[*] allocations[%d] = %p\n", allocation_index, allocations[allocation_index]);
      {% endif %}
    }

    else if (!strcmp(response, "free")) {
      {% if challenge.num_allocations > 1 %}
        printf("Index: ");
        scanf("%127s", response);
        puts("");
        allocation_index = atoi(response);
        assert(allocation_index < {{ challenge.num_allocations }});
      {% else %}
        allocation_index = 0;
      {% endif %}

      {% if walkthrough %}
        printf("[*] free(allocations[%d])\n", allocation_index);
      {% endif %}
      free(allocations[allocation_index]);

      {% if challenge.null_on_free %}
        {% if walkthrough %}
          printf("[*] allocations[%d] = 0\n", allocation_index);
        {% endif %}
        allocations[allocation_index] = 0;
      {% endif %}
    }

    {% if "puts" in challenge.functions %}
      else if (!strcmp(response, "puts")) {
        {% if challenge.num_allocations > 1 %}
          printf("Index: ");
          scanf("%127s", response);
          puts("");
          allocation_index = atoi(response);
          assert(allocation_index < {{ challenge.num_allocations }});
        {% else %}
          allocation_index = 0;
        {% endif %}

        {% if walkthrough %}
          printf("[*] puts(allocations[%d])\n", allocation_index);
        {% endif %}
        printf("Data: ");
        puts(allocations[allocation_index]);
      }
    {% endif %}

    {% if "echo" in challenge.functions %}
      else if (!strcmp(response, "echo")) {
        {% if challenge.num_allocations > 1 %}
        printf("Index: ");
        scanf("%127s", response);
        puts("");
        allocation_index = atoi(response);
        assert(allocation_index < {{ challenge.num_allocations }});
        {% else %}
        allocation_index = 0;
        {% endif %}

        printf("Offset: ");
        scanf("%127s", response);
        puts("");
        offset = atoi(response);

        {% if walkthrough %}
        printf("[*] echo(allocations[%d], %d)\n", allocation_index, offset);
        {% endif %}
        echo(allocations[allocation_index], offset);
      }
    {% endif %}

    {% if "safe_read" in challenge.functions %}
      else if (!strcmp(response, "safe_read")) {
        {% if challenge.num_allocations > 1 %}
          printf("Index: ");
          scanf("%127s", response);
          puts("");
          allocation_index = atoi(response);
          assert(allocation_index < {{ challenge.num_allocations }});
        {% else %}
          allocation_index = 0;
        {% endif %}

        {% if walkthrough %}
          printf("[*] safe_read(0, allocations[%d])\n", allocation_index);
        {% endif %}
        read(0, allocations[allocation_index], allocations_size[allocation_index]);
        puts("");
      }
    {% endif %}


    {% if "safe_write" in challenge.functions %}
      else if (!strcmp(response, "safe_write")) {

        if (stdout_file == NULL) {
          stdout_file = fdopen(1, "w");
        }

        {% if challenge.num_allocations > 1 %}
        printf("Index: ");
        scanf("%127s", response);
        puts("");
        allocation_index = atoi(response);
        assert(allocation_index < {{ challenge.num_allocations }});
        {% else %}
        allocation_index = 0;
        {% endif %}
        {% if walkthrough %}
        printf("[*] safe_write(allocations[%d])\n", allocation_index);
        {% endif %}
        fwrite(allocations[allocation_index], 1, allocations_size[allocation_index], stdout_file);
        fwrite("\n", 1, 1, stdout_file);
        fflush(stdout_file);
      }
    {% endif %}

    {% if "scanf" in challenge.functions %}
      else if (!strcmp(response, "scanf")) {
        {% if challenge.num_allocations > 1 %}
          printf("Index: ");
          scanf("%127s", response);
          puts("");
          allocation_index = atoi(response);
          assert(allocation_index < {{ challenge.num_allocations }});
        {% else %}
          allocation_index = 0;
        {% endif %}

        {% if challenge.dont_scanf_0s %}
          if (malloc_usable_size(allocations[allocation_index]) == 0) {
            continue;
          }
        {% endif %}

        sprintf(response, "%%%us", malloc_usable_size(allocations[allocation_index]));
        {% if walkthrough %}
          printf("[*] scanf(\"%%%us\", allocations[%d])\n", malloc_usable_size(allocations[allocation_index]), allocation_index);
        {% endif %}
        scanf(response, allocations[allocation_index]);
        puts("");
      }
    {% endif %}

    {% if "read" in challenge.functions %}
      else if (!strcmp(response, "read")) {
        {% if challenge.num_allocations > 1 %}
          printf("Index: ");
          scanf("%127s", response);
          puts("");
          allocation_index = atoi(response);
          assert(allocation_index < {{ challenge.num_allocations }});
        {% else %}
          allocation_index = 0;
        {% endif %}

        printf("Size: ");
        scanf("%127s", response);
        puts("");
        size = atoi(response);

        {% if walkthrough %}
          printf("[*] read(0, allocations[%d], %d)\n", allocation_index, size);
        {% endif %}
        read(0, allocations[allocation_index], size);
        puts("");
      }
    {% endif %}

    {% if "read_flag" in challenge.functions %}
      else if (!strcmp(response, "read_flag")) {
        for (int i = 0; i < {{ challenge.num_flag_buffer_allocs }}; i++) {
          {% if walkthrough %}
            printf("[*] flag_buffer = malloc(%d)\n", flag_buffer_size);
          {% endif %}
          flag_buffer = malloc(flag_buffer_size);
          {% if "puts_flag" in challenge.functions %}
            flag_buffer->can_puts = 0;
          {% endif %}
          {% if walkthrough or challenge.print_malloc_pointers %}
            printf("[*] flag_buffer = %p\n", flag_buffer);
          {% endif %}
        }

        {% if "puts_flag" in challenge.functions %}
          read(open("/flag", 0), flag_buffer->data, 128);
        {% else %}
          read(open("/flag", 0), flag_buffer, 128);
        {% endif %}

        {% if walkthrough %}
          printf("[*] read the flag!\n");
        {% endif %}
      }
    {% endif %}

    {% if "puts_flag" in challenge.functions %}
      else if (!strcmp(response, "puts_flag")) {
        if (!flag_buffer->can_puts) {
          printf("Not authorized!\n");
          continue;
        }

        puts(flag_buffer->data);
      }
    {% endif %}

    {% if "send_flag" in challenge.functions %}
      else if (!strcmp(response, "send_flag")) {
        printf("Secret: ");
        scanf("%127s", response);
        puts("");
        if (!memcmp(response, secret.secret, {{ challenge.secret_size }})) {
          printf("Authorized!\n");
          win();
        }
        else {
          printf("Not authorized!\n");
          continue;
        }
      }
    {% endif %}

    {% if "stack_free" in challenge.functions %}
      else if (!strcmp(response, "stack_free")) {
        {% if walkthrough %}
        printf("[*] free(%p)\n", {{ stack_buffer }} + 64);
        {% endif %}
        free({{ stack_buffer }} + 64);
      }
    {% endif %}

    {% if "stack_scanf" in challenge.functions %}
      else if (!strcmp(response, "stack_scanf")) {
        {% if walkthrough %}
        printf("[*] scanf(\"%%127s\", %p)\n", {{ stack_buffer }});
        {% endif %}
        scanf("%127s", {{ stack_buffer }});
        puts("");
      }
    {% endif %}

    {% if "stack_malloc_win" in challenge.functions %}
      else if (!strcmp(response, "stack_malloc_win")) {
        {% if walkthrough %}
          printf("[*] if (malloc(%d) == %p) win()\n", {{ challenge.stack_malloc_win_size }}, {{ stack_buffer }} + 64);
          printf("[*] malloc_usable_size(malloc(%d)) = %d\n", {{ challenge.stack_malloc_win_size }}, {{ challenge.stack_malloc_win_size_usable }});
        {% endif %}
        flag_buffer = malloc({{ challenge.stack_malloc_win_size }});
        {% if walkthrough %}
          printf("[*] malloc(%d) = %p\n", {{ challenge.stack_malloc_win_size }}, flag_buffer);
        {% endif %}
        if (flag_buffer == ({{ stack_buffer }} + 64))
          win();
      }
    {% endif %}

    else if (!strcmp(response, "quit")) {
      break;
    }

    else {
      printf("Unrecognized choice!\n");
      break;
    }
  }
{% endblock %}
