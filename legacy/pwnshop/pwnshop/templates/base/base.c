#define _GNU_SOURCE 1

#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include <assert.h>
#include <libgen.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <sys/signal.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <sys/sendfile.h>
#include <sys/prctl.h>
#include <sys/personality.h>
#include <arpa/inet.h>

{% if challenge.threaded_server %}
  __thread FILE *thread_stdin;
  __thread FILE *thread_stdout;

  #define scanf(...) fscanf(thread_stdin, __VA_ARGS__)
  #define printf(...) fprintf(thread_stdout, __VA_ARGS__)

  #include <semaphore.h>
  #include <pthread.h>
{% endif %}

{% block includes %}
{% endblock %}

{% if challenge.bin_padding %}
  void bin_padding()
  {
    asm volatile (".rept {{ challenge.bin_padding }}; nop; .endr");
  }
{% endif %}

{% if challenge.disable_aslr %}
  {% include "disable_aslr.c" %}
{% endif %}

{% if challenge.win_function %}
  {% if challenge.win_function_authed %}
    void win_authed(int token)
  {% elif challenge.win_function_aligned %}
    void __attribute__ ((aligned (1 << 8))) win()
  {% else %}
    void win()
  {% endif %}
  {
    {% if challenge.static_win_function_variables %}static {% endif %}char flag[256];
    {% if challenge.static_win_function_variables %}static {% endif %}int flag_fd;
    {% if challenge.static_win_function_variables %}static {% endif %}int flag_length;

    {% if challenge.win_function_broken %}
    {
      int *i = 0;
      (*i)++;
    }
    {% endif %}

    {% if challenge.win_function_authed %}
      if (token != 0x1337) {
        puts("win_authed: uthentication check failed. No flag for you!");
        return;
      }
    {% endif %}

    {% if challenge.win_message %}puts("{{challenge.win_message}}");{% endif %}
    {% for _ in range(challenge.win_repeats or 1) %}
    flag_fd = open("/flag", 0);
    if (flag_fd < 0) {
        printf("\n  ERROR: Failed to open the flag -- %s!\n", strerror(errno));
        if (geteuid() != 0) {
            printf("  Your effective user id is not 0!\n");
            printf("  You must directly run the suid binary in order to have the correct permissions!\n");
        }
        exit(-1);
    }
    flag_length = read(flag_fd, flag, sizeof(flag));
    if (flag_length <= 0) {
        printf("\n  ERROR: Failed to read the flag -- %s!\n", strerror(errno));
        exit(-1);
    }
    {% set stdout = "fileno(thread_stdout)" if challenge.threaded_server else "1"%}
    write({{ stdout }}, flag, flag_length);
    printf("\n\n");
    {% endfor %}
  }
{% endif %}

{% block globals %}
  {% if challenge.require_vm %}
    char hostname[128];
  {% endif %}
{% endblock %}

{% if self.challenge_function() | trim %}
  {% if challenge.challenge_function_inline %}
    int inline __attribute__((always_inline)) challenge(int argc, char **argv, char **envp)
  {% else %}
    int challenge(int argc, char **argv, char **envp)
  {% endif %}
  {
    {% block challenge_function %}
    {% endblock %}
  }
{% endif %}

{% if challenge.threaded_server %}
  struct thread_args {
    int client_fd;
    int argc;
    char **argv;
    char **envp;
  };

  int run_thread(struct thread_args *thread_args) {
      {% if challenge.run_thread_padding %}
        char pad [{{ 0x20 }}];
      {% endif %}
      int result;
      thread_stdin = fdopen(thread_args->client_fd, "r");
      thread_stdout = fdopen(thread_args->client_fd, "w");
      setvbuf(thread_stdin, NULL, _IONBF, 0);
      setvbuf(thread_stdout, NULL, _IONBF, 0);
      result = challenge(thread_args->argc, thread_args->argv, thread_args->envp);
      fclose(thread_stdin);
      fclose(thread_stdout);
      return result;
  }

  void sigpipe_handler(int signum)
  {
      pthread_exit(0);
  }

  #undef scanf
  #undef printf
{% endif %}

{% if challenge.vbuf_in_constructor %}
void __attribute__ ((constructor)) disable_buffering() {
       setvbuf(stdin, NULL, _IONBF, 0);
       setvbuf(stdout, NULL, _IONBF, 1);
}
{% endif %}

int main(int argc, char **argv, char **envp)
{
  {% if challenge.vbuf_in_main %}
  setvbuf(stdin, NULL, _IONBF, 0);
  setvbuf(stdout, NULL, _IONBF, 0);
  {% endif %}

  {% if challenge.print_greeting %}
  printf("###\n");
  printf("### Welcome to %s!\n", argv[0]);
  printf("###\n");
  printf("\n");
  {% endif %}

  {% if challenge.stack_goodbye %}
    char goodbye[] = "### Goodbye!";
  {% endif %}

  {% if challenge.require_vm %}
    gethostname(hostname, 128);
    if (strstr(hostname, "~") && !strstr(hostname, "vm_"))
    {
       puts("ERROR: in the dojo, this challenge MUST run in virtualization mode.");
       puts("Please run `vm connect` to launch and connect to the Virtual Machine, then run this challenge inside the VM.");
       puts("You can tell when you are running inside the VM by looking at the hostname in your shell prompt:.");
       puts("if it starts with \"vm_\", you are executing inside the Virtual Machine.");
       puts("");
       puts("You can connect to the VM from multiple terminals by launching `vm connect` in each terminal, and all files");
       puts("are shared between the VM and the normal container.");
       exit(1);
    }
  {% endif %}

  {% if challenge.fork_server or challenge.threaded_server %}
    {{ "This challenge is listening for connections on TCP port 1337." | layout_text }}
    {% if challenge.fork_server %}
      {{ "The challenge supports unlimited sequential connections." | layout_text }}
    {% elif challenge.threaded_server %}
      {{ "The challenge supports unlimited parallel connections." | layout_text }}
    {% endif %}

    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    int server_opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &server_opt, sizeof(server_opt));
    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(1337);
    bind(server_fd, (struct sockaddr *) &server_addr, sizeof(server_addr));
    listen(server_fd, 1);

    {% if challenge.threaded_server %}
      signal(SIGPIPE, sigpipe_handler);
    {% endif %}

    {% if self.initialize_server() | trim %}
      {% block initialize_server %}
      {% endblock %}
    {% endif %}

    while (true) {
      int client_fd = accept(server_fd, NULL, NULL);
      // puts("Connection accepted!");

      {% if challenge.fork_server %}
        if (fork()) {
          close(client_fd);
          wait(0);
        }
        else {
          dup2(client_fd, 0);
          dup2(client_fd, 1);
          dup2(client_fd, 2);
          close(server_fd);
          close(client_fd);
          break;
        }
      {% elif challenge.threaded_server %}
        pthread_t thread;
        struct thread_args *thread_args = malloc(sizeof(struct thread_args));
        thread_args->client_fd = client_fd;
        thread_args->argc = argc;
        thread_args->argv = argv;
        thread_args->envp = envp;
        pthread_create(&thread, NULL, run_thread, thread_args);
      {% endif %}
    }
  {% endif %}

  {% if not challenge.threaded_server %}
    {% block main %}
    {% endblock %}

    {% if self.challenge_function() | trim %}
      challenge(argc, argv, envp);
    {% endif %}
  {% endif %}

  {% if challenge.stack_goodbye %}
    puts(goodbye);
  {% elif challenge.constant_goodbye %}
    printf("### Goodbye!\n");
  {% endif %}
}
