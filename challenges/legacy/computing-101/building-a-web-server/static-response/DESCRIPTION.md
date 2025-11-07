Now that your server can establish connections, it’s time to learn how to send data.
In this challenge, your goal is to send a fixed HTTP response (`HTTP/1.0 200 OK\r\n\r\n`) to any client that connects.
You will use the [write](https://man7.org/linux/man-pages/man2/write.2.html) syscall, which requires a file descriptor, a pointer to a data buffer, and the number of bytes to write.
This exercise is important because it teaches you how to format and deliver data over the network.
