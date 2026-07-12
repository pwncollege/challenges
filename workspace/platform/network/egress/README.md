# Workspace egress

Workspace traffic is filtered on each workspace veth. The host assigns a
synthetic address to the platform-owned `pwn-egress0` dummy interface, and the
veth policy allows only DNS, HTTP, and HTTPS traffic to that address plus
replies from the workspace agent.

The default policy allows only `example.com`; NixOS hosts can override it with
`services.pwn-workspace.egressDomains`. Exact names and conventional
leftmost-label wildcards are supported, and an empty list denies all domains.
The egress service returns the
synthetic address for allowed DNS names and reverse proxies their HTTP and
HTTPS traffic from the host network. All other DNS names and direct
destinations are blocked.

At startup, the egress service generates ephemeral leaf certificates for the
configured patterns and signs them with the checked-in CA private key. The key
is intentionally not secret: the public CA is part of the workspace runtime
closure and is trusted only there.
