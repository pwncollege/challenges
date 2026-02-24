Previously, your server served just one GET request before terminating.
Now, you will modify it so that it can handle multiple GET requests sequentially.
This involves wrapping the accept-read-write-close sequence in a loop.
Each time a client connects, your server will accept the connection, process the GET request, and then cleanly close the client session while remaining active for the next request.
This iterative approach is essential for building a persistent server.
