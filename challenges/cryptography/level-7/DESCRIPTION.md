Diffie-Hellman allow Alice and Bob to generate a single (but uncontrolled) shared secret with no pre-shared secret information.
Next, we'll learn about another cryptosystem, [RSA (Rivest–Shamir–Adleman)](https://en.wikipedia.org/wiki/RSA_(cryptosystem)), that allows Alice and Bob to generate arbitrary amounts of controlled messages, with no pre-shared secret information!

RSA uses a clever interaction of modular exponentiation (which you've experienced in DH) and [Euler's Theorem](https://en.wikipedia.org/wiki/Euler%27s_theorem) to give Bob or Alice _asymmetric_ control over an entire finite field.
Alice generates two primes, `p` and `q`, _and keeps them secret_, then multiplies them to create `n = p*q`, which Alice publishes to define a Finite Field modulo `n`.
Euler's Theorem and knowledge of `p` and `q` gives Alice, _and only Alice_, full abilities within this specific field (which is a difference from DH, where all actors have equal capabilities in the field!).

Euler's Theorem tells us that operations _in an exponent_ of a field modulo `p*q` (e.g., the `e*d` of `m**(e*d) mod n`) take place in the field of `(p-1)*(q-1)`.
The _why_ of this theorem is some advanced math stuff that, to be honest, few people understand, but the results are interesting.
Computing `(p-1)*(q-1)` is trivial for Alice (armed with knowledge of `p` and `q`) but impossible to anyone else (assuming that `p` and `q` are large), because the human race lacks an efficient algorithm to factor products of large prime numbers!

Recall that `e*d` in the exponent of `m**(e*d) mod n`?
For any `e`, knowing `(p-1)*(q-1)` allows Alice to compute a `d` such that `e*d == 1`.
While this seems silly, it is the core of RSA.
Alice chooses a number `e` (typically fairly small to reduce computation costs, but not too small to cause certain security issues) and computes the corresponding multiplicative inverse `d`.
This leads to encryption of plaintext `m` (`m**e mod n == c`) and decryption! `c**d mod n == (m**e)**d mod n == m**(e*d) mod n == m**1 mod n == m`.
Rather than DH's single and uncontrolled `s`, RSA messages `m` can be chosen arbitrarily (up to the size of `n`, as the field is unable to represent larger numbers).

RSA is _asymmetric_.
Alice shares `n` and `e` as the public key, and keeps `d` as the private key.
Knowing `n` and `e`, Bob can encrypt messages and send them to Alice, and only Alice can decrypt them.
Since `e*d == d*e`, Alice _can_ use `d` to encrypt messages, but _anyone_ can decrypt them, since `e` is public.
This might sound silly, but it is useful for, e.g., attesting that a given message could come only from Alice, since knowledge of `d` is required for this.

To respond to Bob, Alice would need Bob's own public key, which would be _Bob's_ `n` (different from Alice's `n`, using Bob's own secret `p` and `q`!) and `e` (which is typically the same smallest-safe value, currently `65537` but subject to change as new attacks are found).

In this challenge you will decrypt a secret encrypted with RSA (Rivest–Shamir–Adleman).
You will be provided with both the public key and private key this time, to get a feel for how all this works.
Go for it!
