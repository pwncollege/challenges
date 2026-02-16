In this challenge, you’ll begin your journey into networking by creating a socket using the [socket](https://man7.org/linux/man-pages/man2/socket.2.html) syscall.
A socket is the basic building block for network communication; it serves as an endpoint for sending and receiving data.
When you invoke [socket](https://man7.org/linux/man-pages/man2/socket.2.html), you provide three key arguments: the domain (for example, `AF_INET` for IPv4), the type (such as `SOCK_STREAM` for TCP), and the protocol (usually set to `0` to choose the default).
Mastering this syscall is important because it lays the foundation for all subsequent network interactions.

----
**NOTE:**
Looking through documentation, the arguments of the system calls are listed as names in all capitals.
For instance, we may wish to call `socket(AF_INET, SOCK_STREAM, 0)` but we cannot simply perform `mov rdi, AF_INET`: `AF_INET` is simply not a concept at the assembly level.
We need to find the integer which corresponds to `AF_INET`.
These numbers are not even found in the man pages, but these numbers do exist on your machine.
Check out the `/usr/include` directory.
All the system's general-use include files for C programming are placed here. (For those who have written C, think of any header files you've included in your code "`#include <stdio.h>`". All those Functions and constants are defined somewhere here).
Since C is compiled to assembly, these numbers are present somewhere in this directory.
Rather than manually searching, you can [grep](https://pwn.college/linux-luminarium/commands/) for them.
