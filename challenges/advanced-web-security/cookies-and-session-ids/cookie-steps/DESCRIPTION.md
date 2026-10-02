A cookie can carry progress through a sequence of requests.
If your client forgets that cookie, the next request loses the state needed to continue.

Follow this application's trail of GET parameters while keeping its cookies, and collect the flag cookie at the end.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
