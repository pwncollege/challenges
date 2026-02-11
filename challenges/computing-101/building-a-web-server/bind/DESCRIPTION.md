After creating a socket, the next step is to assign it a network identity.
In this challenge, you will use the [bind](https://man7.org/linux/man-pages/man2/bind.2.html) syscall to connect your socket to a specific IP address and port number.
The call requires you to provide the socket file descriptor, a pointer to a `struct sockaddr` (specifically a `struct sockaddr_in` for IPv4 that holds fields like the address family, port, and IP address), and the size of that structure.
Binding is essential because it ensures your server listens on a known address, making it reachable by clients.
