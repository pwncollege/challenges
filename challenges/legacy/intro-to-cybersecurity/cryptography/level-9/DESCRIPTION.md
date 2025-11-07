As you saw, raw RSA signatures are a bad idea, as they can be forged.
In practice, what people sign are [_cryptographic hashes_](https://en.wikipedia.org/wiki/Cryptographic_hash_function) of things.
A hash is a one-way function that takes an arbitrary amount of input (e.g., bytes or gigabytes or more) and outputs a short (e.g., 32 bytes) of output hash.
Any changes in the input to the hash will _diffuse_ all over the resulting cryptographic hash in a way that is not reversible.

Thus, secure hashes are a good representation for the original data: if Alice signs a hash of a message, that message can be seen as being signed as well.
Better yet, since hashes are not controllably reversible or modifiable, an attacker being able to modify a hash does not allow them to forge a signature on a new message.

The bane of cryptographic hashing algorithms is _collision_.
If an attacker can craft two messages that hash to the same thing, the security of any system that depends on the hash (such as the RSA signature scheme described above) might be compromised.
For example, consider that the security of bitcoin depends fully on the collision resistance of SHA256...

While full collisions of SHA256 don't exist, some applications use _partial_ hash verification.
This is not a great practice, as it makes it easier to brute-force a collision.

In this challenge you will do just that, hashing data with a Secure Hash Algorithm (SHA256).
You will find a small hash collision.
Your goal is to find data, which when hashed, has the same hash as the secret.
Only the first 3 bytes of the SHA256 hash will be checked.
