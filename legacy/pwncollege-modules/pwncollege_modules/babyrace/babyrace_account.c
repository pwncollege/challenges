{% extends "base/base.c" %}

{% set walkthrough_pause %}
  {% if walkthrough %}
    printf("Paused (press enter to continue)\n");
    scanf("%7s", pause_buffer);
  {% endif %}
{% endset %}

{% block globals %}
  {% if walkthrough %}
    char pause_buffer[8];
  {% endif %}

  {% if challenge.login %}
    unsigned int privilege_level = 0;
  {% endif %}

  {% if challenge.signal %}
    void timeout_handler(int signum)
    {
      puts("Logging out due to timeout.");
      privilege_level = 0;
    }
  {% endif %}

  {% if challenge.message %}
    char global_message[1024];

    {% if challenge.atomic_broadcast %}
      sem_t global_message_mutex;
    {% endif %}

    void broadcast_message(char *message, int length)
    {
      {% if challenge.atomic_broadcast %}
        sem_wait(&global_message_mutex);
      {% endif %}

      for (int i = 0; i < length; i++) {
        {% if walkthrough %}
          printf("[*] global_message[%d] = message[%d]\n", i, i);
        {% endif %}
        {{ walkthrough_pause }}
        global_message[i] = message[i];
      }
      global_message[length] = '\0';

      {% if challenge.atomic_broadcast %}
        sem_post(&global_message_mutex);
      {% endif %}
    }
  {% endif %}
{% endblock %}

{% block initialize_server %}
  {% if challenge.atomic_broadcast %}
    sem_init(&global_message_mutex, 0, 1);
  {% endif %}
{% endblock %}

{% block challenge_function %}
  char response[128];

  {% if challenge.signal %}
    signal(SIGALRM, timeout_handler);
  {% endif %}

  while (true) {
    {% if challenge.login %}
      printf("Privilege level: %d\n", privilege_level);
    {% endif %}

    {% if challenge.login %}
      printf("[*] Function (login/logout/win_authed/quit): \n");
    {% elif challenge.message %}
      printf("[*] Function (send_message/send_redacted_flag/receive_message/quit): \n");
    {% endif %}

    scanf("%127s", response);

    if (strcmp(response, "quit") == 0) {
        break;
    }

    {% if challenge.login %}
      else if (strcmp(response, "login") == 0) {
        {% if walkthrough %}
          printf("Privilege level set to 1.\n");
        {% endif %}

        {{ walkthrough_pause }}

        privilege_level = 1;

        {% if challenge.signal %}
          {% if walkthrough %}
            printf("You will be logged out in 10 minutes!\n");
          {% endif %}
          alarm(600);
        {% endif %}
      }

      else if (strcmp(response, "logout") == 0) {
        if (privilege_level != 0) {
          printf("Dropping one privilege level.\n");

          {{ walkthrough_pause }}

          privilege_level--;
        }
        else {
          {% if walkthrough %}
            printf("You are not logged in!\n");
          {% endif %}
        }
      }

      else if (strcmp(response, "win_authed") == 0) {
        if (privilege_level == 0) {
          printf("You are not logged in!\n");
        }
        else if (privilege_level == 1) {
          printf("Your privilege level is too low!\n");
        }
        else {
          win();
        }
      }

    {% elif challenge.message %}
      else if (strcmp(response, "send_message") == 0) {
        printf("Message: ");
        scanf("%127s", response);
        printf("\n");
        broadcast_message(response, strlen(response));
      }

      else if (strcmp(response, "send_redacted_flag") == 0) {
        char redacted_flag[512] = "REDACTED: ";
        int flag_length = read(open("/flag", 0), redacted_flag + 11, 256);
        broadcast_message(redacted_flag, flag_length + 11);
      }

      else if (strcmp(response, "receive_message") == 0) {
        {% if challenge.receive_printf %}
          printf("Message: %s", global_message);
        {% else %}
          printf("Message: ");
          write(fileno(thread_stdout), global_message, strlen(global_message));
        {% endif %}
      }
    {% endif %}

    else {
      printf("Unrecognized choice!\n");
      continue;
    }
  }
{% endblock %}
