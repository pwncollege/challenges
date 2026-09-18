The third field of the request line is the protocol version, and it is a token like any other.
Clients treat it as fixed: `curl` lets you choose between HTTP/1.0 and HTTP/1.1, but not type an arbitrary token into that slot.
To send a version no client will offer you, write the request line yourself.
This service names the version it speaks.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
