{% extends "base/base.c" %}

{% block includes %}
{% endblock %}

{% block globals %}
  struct {
    char padding[256];
    char *allocations[{{ challenge.num_allocations }}];
    {% if "safe_read" in challenge.functions or "safer_read" in challenge.functions or "read_copy" in challenge.functions or challenge.null_on_free %}
      int sizes[{{ challenge.num_allocations }}];
    {% endif %}
    {% if challenge.read_flag_to_bss %}
      {% if "read_to_global" in challenge.functions %}
        char writable_global[{{ challenge.global_buff_size }}];
      {% endif %}
      char flag_buf[128];
    {% endif %}
  } alloc_struct;
  {% if "read_copy" in challenge.functions %}
    char strcpy_scratch[{{ challenge.max_alloc_size + 1 }}];
  {% endif %}

  {% if "send_flag" in challenge.functions %}
    int authenticated;
  {% endif %}

{% endblock %}

{% block main %}
  char response[128];
  {% if "send_flag" in challenge.functions %}
    authenticated = 0;
  {% endif %}
  unsigned int allocation_index;
  unsigned int size;
  char *flag_buffer;
  size_t flag_buffer_size = {{ challenge.flag_buffer_size }};

  {% if walkthrough %}
    {% filter layout_text_walkthrough %}
      This challenge allows you to perform various heap operations, some of which may involve the flag.
    {% endfilter %}
    printf("This challenge can manage up to %d unique allocations.\n\n", {{ challenge.num_allocations }});
  {% endif %}

  {% if challenge.malloc_flag_at_start %}
    srand((int)time(NULL));
    for (int i = 0; i < rand() % 100; i++) {
      flag_buffer = malloc(flag_buffer_size);
    }

    flag_buffer = malloc(flag_buffer_size);
    // This is not a walkthough leak
    printf("Reading the flag into %p.\n", flag_buffer);
    read(open("/flag", 0), flag_buffer, 128);
  {% endif %}
  {% if challenge.read_flag_to_bss %}
    printf("Reading the flag into %p.\n", alloc_struct.flag_buf);
    read(open("/flag", 0), alloc_struct.flag_buf, 128);
  {% endif %}

  while (true) {
    puts("");
    printf("[*] Function ({{ challenge.functions_description }}): ");
    scanf("%127s", response);
    puts("");

    if (!strcmp(response, "quit")) {
      break;
    }
    {% if "malloc" in challenge.functions %}
      else if (!strcmp(response, "malloc")) {
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

        {% if challenge.max_alloc_size %}
          if (size > {{ challenge.max_alloc_size }}) {
            {% if walkthrough %}
              printf("[!] Max allocation size allowed is 0x%x\n", {{ challenge.max_alloc_size }});
            {% endif %}
            continue;
          }
        {% endif %}

        {% if challenge.min_alloc_size %}
          if (size < {{ challenge.min_alloc_size }}) {
            {% if walkthrough %}
              printf("[!] Minimum allocation size allowed is 0x%x\n", {{ challenge.min_alloc_size }});
            {% endif %}
            continue;
          }
        {% endif %}

        {% if walkthrough %}
          printf("[*] allocations[%d] = malloc(%d)\n", allocation_index, size);
        {% endif %}
        alloc_struct.allocations[allocation_index] = malloc(size);
      {% if "safe_read" in challenge.functions or "safer_read" in challenge.functions or "read_copy" in challenge.functions %}
          alloc_struct.sizes[allocation_index] = size;
        {% endif %}
        {% if walkthrough or challenge.print_malloc_pointers %}
          printf("[*] allocations[%d] = %p\n", allocation_index, alloc_struct.allocations[allocation_index]);
        {% endif %}
      }
    {% endif %}

    {% if "calloc" in challenge.functions %}
      else if (!strcmp(response, "calloc")) {
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
        {% if challenge.max_alloc_size %}
          if (size > {{ challenge.max_alloc_size }}) {
            {% if walkthrough %}
              printf("[!] Max allocation size allowed is 0x%x\n", {{ challenge.max_alloc_size }});
            {% endif %}
            continue;
          }
        {% endif %}

        {% if challenge.min_alloc_size %}
          if (size < {{ challenge.min_alloc_size }}) {
            {% if walkthrough %}
              printf("[!] Minimum allocation size allowed is 0x%x\n", {{ challenge.min_alloc_size }});
            {% endif %}
            continue;
          }
        {% endif %}
        {% if walkthrough %}
          printf("[*] allocations[%d] = calloc(1, %d)\n", allocation_index, size);
        {% endif %}
        alloc_struct.allocations[allocation_index] = calloc(1, size);
        {% if "safe_read" in challenge.functions or "safer_read" in challenge.functions %}
          alloc_struct.sizes[allocation_index] = size;
        {% endif %}
        {% if walkthrough or challenge.print_malloc_pointers %}
          printf("[*] allocations[%d] = %p\n", allocation_index, alloc_struct.allocations[allocation_index]);
        {% endif %}
      }
    {% endif %}

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
      free(alloc_struct.allocations[allocation_index]);

      {% if challenge.null_on_free %}
        alloc_struct.allocations[allocation_index] = 0;
        alloc_struct.sizes[allocation_index] = 0;
      {% elif challenge.zero_size_on_free %}
        alloc_struct.sizes[allocation_index] = 0;
      {% endif %}
      {% if walkthrough %}
        printf("[*] allocations[%d] = %p\n", allocation_index, alloc_struct.allocations[allocation_index]);
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
        {% if challenge.dont_puts_0_size %}
          if (alloc_struct.sizes[allocation_index] == 0) {
            printf("Cannot puts freed indexes!\n");
            continue;
          }
        {% endif %}
        {% if challenge.dont_puts_0s %}
          if (malloc_usable_size(alloc_struct.allocations[allocation_index]) == 0) {
            continue;
          }
        {% endif %}

        {% if walkthrough %}
          printf("[*] puts(allocations[%d])\n", allocation_index);
        {% endif %}
        printf("Data: ");
        puts(alloc_struct.allocations[allocation_index]);
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
          if (malloc_usable_size(alloc_struct.allocations[allocation_index]) == 0) {
            continue;
          }
        {% endif %}

        sprintf(response, "%%%us", malloc_usable_size(alloc_struct.allocations[allocation_index]));
        {% if walkthrough %}
          printf("[*] scanf(\"%%%us\", allocations[%d])\n", malloc_usable_size(alloc_struct.allocations[allocation_index]), allocation_index);
        {% endif %}
        scanf(response, alloc_struct.allocations[allocation_index]);
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
        read(0, alloc_struct.allocations[allocation_index], size);
        puts("");
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

        size = alloc_struct.sizes[allocation_index];

        {% if walkthrough %}
          printf("[*] read(0, allocations[%d], %d)\n", allocation_index, size);
        {% endif %}
        read(0, alloc_struct.allocations[allocation_index], size);
        puts("");
      }
    {% endif %}

    {% if "safer_read" in challenge.functions %}
      else if (!strcmp(response, "safer_read")) {
        {% if challenge.num_allocations > 1 %}
          printf("Index: ");
          scanf("%127s", response);
          puts("");
          allocation_index = atoi(response);
          assert(allocation_index < {{ challenge.num_allocations }});
        {% else %}
          allocation_index = 0;
        {% endif %}

        size = alloc_struct.sizes[allocation_index];

        if (size == 0) {
          printf("Cannot read to freed indexes!\n");
          continue;
        }

        {% if walkthrough %}
          printf("[*] read(0, allocations[%d], %d)\n", allocation_index, size);
        {% endif %}
        read(0, alloc_struct.allocations[allocation_index], size);
        puts("");
      }
    {% endif %}

    {% if "read_copy" in challenge.functions %}
      else if (!strcmp(response, "read_copy")) {
        {% if challenge.num_allocations > 1 %}
          printf("Index: ");
          scanf("%127s", response);
          puts("");
          allocation_index = atoi(response);
          assert(allocation_index < {{ challenge.num_allocations }});
        {% else %}
          allocation_index = 0;
        {% endif %}

        size = alloc_struct.sizes[allocation_index];

        if (size == 0) {
          printf("Cannot read to freed indexes!\n");
          continue;
        }

        {% if walkthrough %}
          printf("[*] read(0, stack_buffer)\n", allocation_index, size);
        {% endif %}
        int readlen = read(0, strcpy_scratch, alloc_struct.sizes[allocation_index]);
        memcpy(alloc_struct.allocations[allocation_index], strcpy_scratch, readlen);
        alloc_struct.allocations[allocation_index][readlen] = '\x00';
        {% if walkthrough %}
          printf("[*] memcpy(allocations[%d], stack_buffer, %d)\n", allocation_index, readlen);
          printf("[*] allocations[%d] = 0x00\n", allocation_index);
        {% endif %}

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

    {% if "send_flag" in challenge.functions %}
    else if (!strcmp(response, "send_flag")) {
      if (authenticated) {
        sendfile(1, open("/flag", O_RDONLY), 0, 64);
      } else{
        printf("Not authenticated!\n");
      }
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

    {% if "read_to_global" in challenge.functions %}
    else if (!strcmp(response, "read_to_global")) {
        printf("read_size: ");
        scanf("%127s", response);
        int read_size = atoi(response);
        read(0, alloc_struct.writable_global, read_size);
    }
    {% endif %}

    else {
      printf("Unrecognized choice!\n");
      break;
    }
  }
{% endblock %}
