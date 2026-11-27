So, you now (hopefully!) understand the use of AES and the various hurdles, but there has been one thing that we have not considered.
If person A (commonly refered to as [Alice](https://en.wikipedia.org/wiki/Alice_and_Bob)) wants to encrypt some data and send it to person B (commonly refered to as Bob) using AES, they must first agree on a key.
If Alice and Bob see each other in person, one might write the key down and hand it to the other.
But this rarely happens --- typically, the key must be established remotely, with Alice and Bob on either end of a (not yet encrypted!) network connection.
In these common cases, Alice and Bob must securely generate a key even if they are being eavesdropped upon (think: network sniffing)!
Fun fact: typically, the *eave*sdropper is referred to as Eve.

An "oldie but goodie" algorithm for generating a secret key on a non-secret communication channel is the [Diffie-Hellman Key Exchange](https://en.wikipedia.org/wiki/Diffie%E2%80%93Hellman_key_exchange)!
DHKE uses the power of mathematics (specifically, Finite Fields) to come up with a key.
Let's take it step by step:

1. First, Alice and Bob agree on a large prime number `p` to define their Finite Field (e.g., all further operations occur _modulo `p`_: a context where numbers go from `0` to `p-1`, and then loop around), along with a _root_ `g`, and exchange them in the open, content to let Eve see them.
2. Then, Alice and Bob each generate a _secret_ number (`a` for Alice's and `b` for Bob's).
   These numbers are never shared.
3. Alice computes `A = (g ** a) mod p` (`g` to the `a` power modulo `p`) and Bob computes `B = (g ** b) mod p`.
   Alice and Bob exchange `A` and `B` in the open.
4. At this point, Eve will have `p`, `g`, `A`, and `B`, but will be unable to recover `a` or `b`.
   If it wasn't for the finite field, recovering `a` and `b` would be trivial via a logarithm-base-`g`: `log_g(A) == a` and `log_g(B) == b`.
   However, this does not work in a Finite Field under a modulo because, conceptually, we have no efficient way to determine how many times the `g ** a` computation "looped around" from `p-1` to `0`, and this is needed to compute the logarithm.
   This logarithm-in-a-finite-field problem is called the [Discrete Logarithm](https://en.wikipedia.org/wiki/Discrete_logarithm), and there is no efficient way to solve this without using a quantum computer.
   Quantum computers' ability to solve this problem is the most immediate thing that makes them so dangerous to cryptography.
5. Alice calculates `s = (B ** a) mod p`, and since `B` was `(g ** b) mod p`, this results in `s = ((g ** b) ** a) mod p` or, applying middle school math, `s = (g ** (b*a)) mod p`.
   Bob calculates `s = (A ** b) mod p`, and since `A` was `(g ** a) mod p`, this results in `s = (g ** (a*b)) mod p`. Since `a*b == b*a`, the `s` values computed by both Bob and Alice are equal!
6. Eve _cannot_ compute `s` because Eve lacks `a` or `b`.
   Eve could compute `A ** B == g ** a ** g ** b`, which reduces to something like `g ** (a*(g**b))` and doesn't get Eve any closer to `s`!
   Eve could also compute `A * B == (g ** a) * (g ** b) == g ** (a+b)`, but again, this is not the `s == g ** (a*b)` that Bob and Alice arrived at.
   Eve is out of luck!

Because `A` and `B` are public, they are termed _public keys_, with `a` and `b` being _private keys_.
Furthermore, you may noticed in this level that the prime number `p` that we use is hardcoded and, in fact, there are recommended DHKE [for many bitsizes](https://datatracker.ietf.org/doc/html/rfc3526).
The standardization of these primes allows Alice and Bob to just publish `A` and `B` (though, in practice, `p` is also transmitted to support the use of different `p`s in certain scenarios).



In this challenge you will perform a Diffie-Hellman key exchange.
Good luck!
