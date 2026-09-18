`GET` and `POST` are conventions, not limits.
The method is just the first token of the request line, and a server may route on any token it chooses.
This service ignores every method a browser can produce, and names the one it answers to.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
