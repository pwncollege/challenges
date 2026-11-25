The strength of HTTPS is directly associated with the strength of the crypto.
In this challenge, the HTTPS server uses an RSA certificate with a weak public key.
Specifically, in `N = p * q`, `p` and `q` are too close to each other, which makes it easy to factor `N` and build the private key.

We captured a client fetching the flag from the HTTPS server.
Analyze `/challenge/traffic.pcap`, recover the private key from the server's certificate, and decrypt the traffic to find the flag.
