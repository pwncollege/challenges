In this challenge, your server evolves to handle dynamic content based on HTTP GET requests.
You will first use the [read](https://man7.org/linux/man-pages/man2/read.2.html) syscall to receive the incoming HTTP request from the client socket.
By examining the request line--particularly, in this case, the URL path--you can determine what the client is asking for.
Next, use the [open](https://man7.org/linux/man-pages/man2/open.2.html) syscall to open the requested file and [read](https://man7.org/linux/man-pages/man2/read.2.html) to read its contents.
Send the file contents back to the client using the [write](https://man7.org/linux/man-pages/man2/write.2.html) syscall.
This marks a significant step toward interactivity, as your server begins tailoring its output rather than simply echoing a static message.
