Applications sometimes use request authority to build absolute links.
If that authority is attacker-controlled, a secret reset link can be sent to the wrong host.
Poison the admin's reset link, run `/challenge/victim`, and recover the flag.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
