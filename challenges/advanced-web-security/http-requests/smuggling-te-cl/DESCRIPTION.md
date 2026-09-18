Now reverse the framing disagreement: the frontend follows chunked `Transfer-Encoding`, while the backend follows `Content-Length`.
Desynchronize their request boundaries, reach the protected admin route, and recover the flag.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
