You have seen proxies record client addresses in `X-Forwarded-For`.
An application that trusts this field without a trusted proxy lets the client choose its apparent address.
Exploit that misplaced trust and recover the flag.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
