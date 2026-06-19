From your host at 10.0.0.1, listen on port 31337 for a connection from the remote host at 10.0.0.2.

Once a connection is established, that connection is bidirectional, meaning that both sides can send and receive data.
However, to actually establish the connection, one side must listen for incoming connections, and the other side must connect to that listener.
This time, unlike before, you are the listener.

Review the man page for netcat (`man nc`) to see how to listen for incoming connections.
