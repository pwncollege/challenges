Though the core of the AES crypto algorithm is thought to be secure (not _proven_ to be, though: no one has managed to do that! But no one has managed to significantly break the crypto in the 20+ years of its use, either), this core only encrypts 128-bit (16 byte) blocks at a time.
To actually _use_ AES in practice, one must build a _cryptosystem_ on top of it.

In the previous level, we used the AES-[ECB](https://en.wikipedia.org/wiki/Block_cipher_mode_of_operation#Electronic_codebook_(ECB)) cryptosystem: an Electronic Codebook Cipher where every block is independently encrypted by the same key.
This system is quite simple but, as we will discover here, extremely susceptible to a certain class of attack.

Cryptosystems are held to very high standard of [ciphertext indistinguishability](https://en.wikipedia.org/wiki/Ciphertext_indistinguishability).
That is, an attacker that lacks the key to the cryptosystem should not be able to distinguish between pairs of ciphertext based on the plaintext that was encrypted.
For example, if the attacker looks at ciphertexts `UVSDFGIWEHFBFFCA` and `LKXBFVYASLJDEWEU`, and is able to determine that the latter was produced from the plaintext `EEEEFFFFGGGGHHHH` (or, in fact, figure out _any_ information about the plaintext at all!), the cryptosystem is considered broken.
This property must hold even if the attacker already knows part or all of the plaintext, a setting known as the [Known Plaintext Attack](https://en.wikipedia.org/wiki/Known-plaintext_attack), _or can even control part or all of the plaintext_, a setting known as the [Chosen Plaintext Attack](https://en.wikipedia.org/wiki/Chosen-plaintext_attack)!

ECB is susceptible to both known and chosen plaintext attack.
Because every block is encrypted with the same key, with no other modifications, an attacker can observe identical ciphertext across different blocks that have identical plaintext.
Moreover, if the attacker can choose or learn the plaintext associated with some of these blocks, they can carefully build a mapping from known-plaintext to known-ciphertext, and use that as a lookup table to decrypt other matching ciphertext!

In this level, you will do just this: you will build a codebook mapping from ciphertext to chosen plaintext, then use that to decrypt the flag.
Good luck!

----
**HINT:**
You might find it helpful to automate interactions with this challenge.
You can do so using the `pwntools` Python package.
Check out [this pwntools cheatsheet](https://gist.github.com/anvbis/64907e4f90974c4bdd930baeb705dedf) from a fellow pwn.college student!
