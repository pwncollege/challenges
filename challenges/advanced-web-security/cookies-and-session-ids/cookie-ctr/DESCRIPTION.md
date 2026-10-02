Encrypting a cookie hides its content, but secrecy alone does not make the original content trustworthy.
AES CTR (counter mode) encrypts by XORing plaintext with a keystream.
A change to a ciphertext bit causes the corresponding plaintext bit to change on decryption.
Without authentication, the server cannot detect the manipulated cookie content.

This application encrypts a JSON cookie containing `is_admin: false` with AES-CTR and trusts the decrypted value.
Gain admin access and find the flag!
Run `/challenge/server`, then interact with `http://challenge.localhost/`.
