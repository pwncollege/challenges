Once your socket is listening, it’s time to actively accept incoming connections.
In this challenge, you will use the [accept](https://man7.org/linux/man-pages/man2/accept.2.html) syscall, which waits for a client to connect.
When a connection is established, it returns a new socket file descriptor dedicated to communication with that client and fills in a provided address structure (such as a `struct sockaddr_in`) with the client’s details.
This process is a critical step in transforming your server from a passive listener into an active communicator.
