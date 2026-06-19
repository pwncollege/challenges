{% extends "base/base.c" %}

{% block includes %}
  {% if challenge.flag_seed %}
    {% include "flag_seed.c" %}
  {% endif %}
{% endblock %}

{% block globals %}
  sem_t mutex;
  char *messages[16] = { 0 };
  int stored[16] = { 0 };

  {% if challenge.secret_location == "bss" %}
    struct {
      char padding[ {{ challenge.secret_padding }} ];
      char secret[{{ challenge.secret_size }} + 1];
    } __attribute__ ((aligned (1 << 8), packed)) secret;
  {% endif %}

  {% if challenge.secret_location %}
    void load_secret(char *secret)
    {
      sem_wait(&mutex);
      flag_seed();
      for (int i = 0; i < {{ challenge.secret_size }}; i++)
        secret[i] = (rand() % ('z' - 'a' + 1)) + 'a';
      secret[{{ challenge.secret_size }}] = '\0';
      sem_post(&mutex);
      return;
    }

    bool secret_correct(char *secret)
    {
      char correct[{{ challenge.secret_size }} + 1];
      load_secret(correct);
      bool result = strncmp(secret, correct, {{ challenge.secret_size }}) == 0;
      memset(correct, 0, {{ challenge.secret_size }} + 1);
      return result;
    }
  {% endif %}
{% endblock %}

{% block initialize_server %}
  sem_init(&mutex, 0, 1);

  {% if challenge.secret_location == "env" %}
    char secret[{{ challenge.secret_size }} + 1];

  {% elif challenge.secret_location == "main_heap" %}
    char *secret;
    for (int i = 0; i < {{ challenge.secret_padding_mallocs }}; i++) {
      malloc({{ challenge.secret_size }} + 1);
    }
    secret = malloc({{ challenge.secret_size }} + 1);
  {% endif %}

  {% if walkthrough %}
    {% if challenge.secret_location == "bss" %}
      printf("Storing the secret in the bss.\n");
    {% elif challenge.secret_location == "main_heap" %}
      printf("Storing the secret in the main thread's heap.\n");
    {% endif %}
  {% endif %}

  {% if challenge.secret_location in ["bss", "env", "main_heap"] %}
    load_secret({{ challenge.secret }});
  {% endif %}

  {% if challenge.secret_location == "env" %}
    {% if walkthrough %}
      printf("Storing the secret in the environment.\n");
    {% endif %}
    setenv("secret_value_is", {{ challenge.secret }}, true);
  {% endif %}
{% endblock %}

{% block challenge_function %}
  printf("Welcome to the message server!\n");
  printf("Commands: {{ challenge.functions_description }}.\n");
  char input[1024];
  int idx;

  {% if challenge.secret_location == "thread_heap" %}
    char *secret;
    for (int i = 0; i < {{ challenge.secret_padding_mallocs }}; i++) {
      malloc({{ challenge.secret_size }} + 1);
    }

    secret = malloc({{ challenge.secret_size }} + 1);

  {% elif challenge.secret_location == "thread_stack" %}
    struct {
      char padding[{{ challenge.secret_padding }}];
      char secret[{{ challenge.secret_size }} + 1];
    } __attribute__ ((aligned (1 << 8), packed)) secret;
  {% endif %}

  {% if walkthrough %}
    {% if challenge.secret_location == "thread_heap" %}
      printf("Storing the secret in this thread's heap.\n");
    {% elif challenge.secret_location == "thread_stack" %}
      printf("Storing the secret in this thread's stack.\n");
    {% endif %}
  {% endif %}

  {% if challenge.secret_location in ["thread_heap", "thread_stack"] %}
    load_secret({{ challenge.secret }});
  {% endif %}

  while (true) {
    if (scanf("%1024s", input) == EOF) break;

    if (!strcmp(input, "printf")) {
      if (scanf("%d", &idx) == EOF) break;
      if (printf("MESSAGE: %s\n", stored[idx] ? messages[idx] : "NONE") < 0) break;
    }

    else if (!strcmp(input, "malloc")) {
      if (scanf("%d", &idx) == EOF) break;
      if (!stored[idx]) messages[idx] = malloc(1024);
      stored[idx] = 1;
    }

    else if (!strcmp(input, "scanf")) {
      if (scanf("%d", &idx) == EOF) break;
      scanf("%1024s", stored[idx] ? messages[idx] : input);
    }

    else if (!strcmp(input, "free")) {
      if (scanf("%d", &idx) == EOF) break;
      if (stored[idx]) free(messages[idx]);
      stored[idx] = 0;
    }

    {% if "send_flag" in challenge.functions %}
      else if (!strcmp(input, "send_flag")) {
        printf("Secret: ");
        scanf("%1024s", input);
        if (secret_correct(input)) {
          printf("Authorized!\n");
          win();
        }
        else {
          printf("Not authorized!\n");
        }
      }
    {% endif %}

    else if (!strcmp(input, "quit")) {
        break;
    }

    else {
      printf("Unrecognized choice!\n");
    }
  }

  {% if challenge.early_exit %}
    fclose(thread_stdin);
    fclose(thread_stdout);
    pthread_exit(0);
  {% endif %}
{% endblock %}
