An HTTP/1.1 connection can carry multiple requests, so every component must agree where each request ends.
`Content-Length` counts body bytes, while chunked `Transfer-Encoding` marks the end with a zero-sized chunk.
Here the frontend follows `Content-Length`, but the backend follows chunked framing.
Exploit the boundary disagreement to reach the protected admin route and recover the flag.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
