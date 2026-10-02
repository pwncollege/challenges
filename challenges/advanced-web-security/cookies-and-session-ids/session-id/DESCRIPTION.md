Instead of storing all state in a cookie, a server can store that state itself and give the client a session ID that identifies it.
The client returns the ID with later requests so the server can locate the same session.
Therefore, protecting the (opaque) session ID is important.

Get a session ID from this server and return it in a cookie to receive the flag.
Run `/challenge/server`, then interact with `http://challenge.localhost/`.
