After creating a socket, the next step is to assign it a network identity.
In this challenge, you will use the [bind](https://man7.org/linux/man-pages/man2/bind.2.html) syscall to connect your socket to a specific IP address and port number.
The call requires the socket file descriptor, a pointer to a `struct sockaddr`, and the size of that structure.
For IPv4, the structure is a `struct sockaddr_in`, and `bind` reads the 16 bytes at that pointer as fields:

```text
bytes 0..1    address family, `AF_INET` (`2`)
bytes 2..3    port, in network byte order (`00 50` for port 80)
bytes 4..7    address (`0.0.0.0` is four zero bytes)
bytes 8..15   padding
```

Back in [Opening the Flag, with RIP](/computing-101/hello-hackers/open-read-write-rip-relative), you used stored bytes and passed their address to a syscall.
Here, build the `sockaddr_in` bytes on the stack, pass the stack address as the pointer, and pass `16` as the size.
On 64-bit x86, writing the word value `0x5000` stores the bytes `00 50`, which is port `80` in network byte order.
Binding is essential because it ensures your server listens on a known address, making it reachable by clients.
