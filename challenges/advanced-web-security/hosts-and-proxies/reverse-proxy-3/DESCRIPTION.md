`X-Forwarded-For` represents a chain of hops rather than one address.
A proxy may append its observation to a value that is already present.
Exploit a backend that trusts the wrong end of the chain.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
