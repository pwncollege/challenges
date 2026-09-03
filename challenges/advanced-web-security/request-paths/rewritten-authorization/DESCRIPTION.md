An edge authorization rule protects only the path namespace it checks.
A rewrite can expose the same backend route under another external path.
Exploit that mismatch and recover the flag.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
