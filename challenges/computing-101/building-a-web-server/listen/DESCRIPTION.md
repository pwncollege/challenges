With your socket bound to an address, you now need to prepare it to accept incoming connections.
The [listen](https://man7.org/linux/man-pages/man2/listen.2.html) syscall transforms your socket into a passive one that awaits client connection requests.
It requires the socket’s file descriptor and a backlog parameter, which sets the maximum number of queued connections.
This step is vital because without marking the socket as listening, your server wouldn’t be able to receive any connection attempts.
