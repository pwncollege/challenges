A reverse proxy creates a new connection to its backend.
The backend therefore sees the proxy, not the browser, as its immediate network peer.
Exploit that trust boundary and recover the flag.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
