Proxies often forward a client address in `X-Real-IP`.
That value is trustworthy only when the proxy replaces attacker input.
Exploit the proxy's handling of this header and recover the flag.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
