Diffie–Hellman key exchange lets client and server choose their private exponents and send only a public value in order to negotiate a secret key.
The server gives you a prime `p` and a generator `g`.
Choose a private exponent `a` with `2 <= a < (p - 1) / 2`, then compute your public value `A = g^a mod p`.
The server picks its own exponent `b` and sends `B = g^b mod p`.
You can compute `B^a mod p` and the server can compute `A^b mod p`.

Send a `GET` request to `http://challenge.localhost/` to get `p` and `g` as hexadecimal strings.
Then `POST` JSON to the same URL with a hexadecimal string in the `A` field.
The response gives you `B`, `iv`, and `ciphertext`, all in hexadecimal.

To turn the shared number into an encryption key, encode it as an unsigned, big-endian integer padded to the byte length of `p`.
Run HKDF with SHA-256, no salt, the ASCII info string `pwn.college/dh`, and a 32-byte output.
Decrypt `ciphertext` using AES-CBC with that key and the supplied IV, then remove the PKCS#7 padding.
Submit the flag you decrypt.
