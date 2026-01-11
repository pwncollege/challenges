So, One Time Pads fail when you reuse them.
This is suboptimal: given how careful one has to be when transferring keys, it would be better if the key could be used for more than just a single message!

Enter: the [Advanced Encryption Standard](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard), AES.
AES is relatively new: coming on the scene in 2001.
Like a One-time Pad, AES is _also_ symmetric: the same key is used to encrypt and decrypt.
Unlike a One-time Pad, AES maintains security for multiple messages encrypted with the same key.

In this challenge you will decrypt a secret encrypted with Advanced Encryption Standard (AES).  
AES is what is called a "block cipher", encrypting one plaintext "block" of 16 bytes (128 bits) at a time.
So `AAAABBBBCCCCDDDD` would be a single block of plaintext that would be encrypted into a single block of ciphertext.

AES _must_ operate on complete blocks.
If the plaintext is _shorter_ than a block (e.g., `AAAABBBB`), it will be _padded_ to the block size, and the padded plaintext will be encrypted.

Different AES "modes" define what to do when the plaintext is longer than one block.
In this challenge, we are using the simplest mode: "[Electronic Codebook (ECB)](https://en.wikipedia.org/wiki/Block_cipher_mode_of_operation#Electronic_codebook_(ECB))".
In ECB, each block is encrypted separately with the same key and simply concatenated together.
So if you are encrypting something like `AAAABBBBCCCCDDDDEEEEFFFFGGGGHHHH`, it will be split into two plaintext blocks (`AAAABBBBCCCCDDDD` and `EEEEFFFFGGGGHHHH`), encrypted separately (resulting, let's imagine, in `UVSDFGIWEHFBFFCA` and `LKXBFVYASLJDEWEU`), then concatenated (resulting the ciphertext `UVSDFGIWEHFBFFCALKXBFVYASLJDEWEU`).

This challenge will give you the AES-encrypted flag and the key used to encrypt it.
We won't learn about the internals of AES, in terms of how it actually encrypts the raw bytes.
Instead, we'll learn about different _applications_ of AES, and how they break down in practice.
If you're interested in learning about AES internals, we can highly recommend [CryptoHack](https://cryptohack.org/courses/), an amazing learning resource that focuses on the nitty gritty details of crypto!

Now, go decrypt the flag and score!

----
**HINT:**
We use the [PyCryptoDome](https://www.pycryptodome.org/) library to implement the encryption in this level.
You'll want to read its documentation to figure out how to implement your decryption!
