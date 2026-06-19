int server_fd = socket(AF_INET, SOCK_STREAM, 0);
int option = 1;
setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &option, sizeof(option));
struct sockaddr_in server_addr;
server_addr.sin_family = AF_INET;
server_addr.sin_addr.s_addr = INADDR_ANY;
server_addr.sin_port = htons({% challenge.port %});
bind(server_fd, (struct sockaddr *) &server_addr, sizeof(server_addr));
listen(server_fd, 1);

puts("This challenge is listening for connections on TCP port {% challenge.port %}.");
puts("The challenge supports one connection at a time, but unlimited connections.");

while (true) {
  int input_fd = accept(server_fd, NULL, NULL);
  puts("Connection accepted!");

  if (fork()) {
    wait(0);
  }
  else {
    dup(input_fd, 0);
    dup(input_fd, 1);
    dup(input_fd, 2);
    challenge();
    _exit(0);
  }
}
