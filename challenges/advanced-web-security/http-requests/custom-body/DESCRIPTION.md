A request body carries no delimiter of its own.
The server learns where it ends from `Content-Length` and reads exactly that many bytes, so bytes sent without a count are bytes the server never reads.
This service wants one specific body, and names it.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
