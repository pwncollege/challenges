Werkzeug's `ProxyFix` trusts a configured number of proxy hops from the right of an `X-Forwarded-For` chain.
That count must match the deployed topology.
Exploit the mismatch and recover the flag.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
