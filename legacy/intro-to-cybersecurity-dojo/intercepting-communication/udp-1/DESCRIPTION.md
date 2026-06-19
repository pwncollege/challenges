You're now an expert in TCP, which, as you know, is a great protocol for talking through one connection at a time.
TCP is stable and reliable, but it is fairly complex.
All of that complexity, of course, comes at a performance cost: all the handshakes, ACKs, and so on take time.

As a solution to this, the Internet's inventors came up with UDP: the [User Datagram Packet](https://en.wikipedia.org/wiki/User_Datagram_Protocol).
UDP is a MUCH simpler protocol.
Unlike TCP, which tracks a ton of things, UDP headers simply contain the source port, destination port, length, and a packet checksum.
Super simple!

There are some trade-offs for this simplicity, though.
Without TCP's functionality, UDP lacks the concept of a "connection".
Each packet is not intrinsically linked to any packet, and if this sort of link is desired, the network application itself has to do it.

This makes writing UDP servers and clients a bit strange.
When using UDP sockets, there is no more `s.listen` and `s.accept` for socket `s`: you simply `s.recvfrom` to get data (returning the bytes received and the address of the sender, as retrieved from the UDP packet) and `s.sendto` (taking the bytes to send an the address of the sender).
A single server loop can, thus, handle multiple client interactions all coming together at the same time, but this also makes it easy to mix things up in an insecure way.

In this challenge, you'll make your first UDP connection. 
From your host at 10.0.0.1, connect to the remote host at 10.0.0.2 on port 31337, and send the message: `Hello, World!`.
You can use Python or netcat, but we'd recommend the former, as it'll be more useful in future challenges.
