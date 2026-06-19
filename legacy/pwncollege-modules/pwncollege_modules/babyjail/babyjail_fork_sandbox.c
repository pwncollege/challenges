{% extends "base/base.c" %}

{% block includes %}
  {% if challenge.syscalls_allowed %}
    #include <seccomp.h>
  {% endif %}
{% endblock %}

{% block globals %}
  int child_pid;

  void cleanup(int signal)
  {
    {{ "Time is up: terminating the child and parent!" | layout_text }}
    kill(child_pid, 9);
    kill(getpid(), 9);
  }
{% endblock %}

{% block main %}
  {% filter layout_text %}
    This challenge will fork into a jail.
    Inside of the child process' jail, you will only be able to communicate with the parent process.
    If you want the flag, you must convince the parent process to give it to you.
  {% endfilter %}

  for (int i = 3; i < 10000; i++) close(i);

  {% filter layout_text %}
    Creating a `socketpair` that the child and parent will use to communicate.
    This is a pair of file descriptors that are connected: data written to one can be read from the other, and vice-versa.
  {% endfilter %}

  int file_descriptors[2];
  assert(socketpair(AF_UNIX, SOCK_STREAM, 0, file_descriptors) == 0);
  int parent_socket = file_descriptors[0];
  int child_socket = file_descriptors[1];

  printf("The parent side of the socketpair is FD %d.\n", parent_socket);
  printf("The child side of the socketpair is FD %d.\n", child_socket);

  {{ "Registering a cleanup function that will run 1 second from now and terminate both the parent and child." | layout_text }}
  alarm(1);
  signal(SIGALRM, cleanup);

  {{ "Forking into a parent and child (sandbox) process." | layout_text }}
  child_pid = fork();
  if (!child_pid) {
    {{ "The child will now close itself off from the world, except for the child side of the socketpair." | layout_text }}
    close(0);
    close(1);
    close(2);
    close(parent_socket);

    void *shellcode = mmap((void *)0x1337000, 0x1000, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_PRIVATE|MAP_ANON, 0, 0);
    assert(shellcode == (void *)0x1337000);
    printf("The child mapped 0x1000 bytes for shellcode at %p!\n", shellcode);

    {% include "babyjail/seccomp_init.c" %}

    {% if challenge.syscalls_allowed %}
    assert(seccomp_load(ctx) == 0);
    {% endif %}

    read(child_socket, shellcode, 0x1000);

    write(child_socket, "print_msg:Executing shellcode!", 128);

    ((void(*)())shellcode)();
  }

  else {
    {{ "The parent is reading 0x1000 bytes of shellcode from stdin." | layout_text }}
    char shellcode[0x1000];
    read(0, shellcode, 0x1000);

    {{ "The parent is sending the shellcode to the child." | layout_text }}
    write(parent_socket, shellcode, 0x1000);

    while (true) {
      char command[128] = { 0 };

      {{ "The parent is waiting for a command from the child." | layout_text }}
      int command_size = read(parent_socket, command, 128);
      command[9] = '\0';

      char *command_argument = &command[10];
      int command_argument_size = command_size - 10;

      printf("The parent received command `%.10s` with an argument of %d bytes from the child.\n", command, command_argument_size);

      if (strcmp(command, "print_msg") == 0) {
        puts(command_argument);
      }
      else if (strcmp(command, "read_file") == 0) {
        sendfile(parent_socket, open(command_argument, 0), 0, 128);
      }
      else {
        {{ "Error: unknown command!" | layout_text }}
        break;
      }
    }
  }
{% endblock %}
