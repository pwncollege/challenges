Once you have accepted a connection, the client can send its request through the new socket file descriptor.
You have already used the [`read` syscall](/computing-101/hello-hackers/read) to move bytes from a file descriptor into memory; a connected socket works the same way.
Accept a client, read a nonzero number of request bytes, close the connected socket, and exit cleanly.
