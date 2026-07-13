Now that your server can accept a connection and read its request, it’s time to learn how to send data.
After reading the request, send the fixed HTTP response `HTTP/1.0 200 OK\r\n\r\n` to the client.
You will use the [write](https://man7.org/linux/man-pages/man2/write.2.html) syscall, which requires a file descriptor, a pointer to a data buffer, and the number of bytes to write.
This exercise is important because it teaches you how to format and deliver data over the network.
