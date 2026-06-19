Okay, hopefully we agree that ECB is a bad block cipher mode.
Let's explore one that isn't _so_ bad: [Cipher Block Chaining (CBC)](https://en.wikipedia.org/wiki/Block_cipher_mode_of_operation#Cipher_block_chaining_(CBC)).
CBC mode encrypts blocks sequentially, and before encrypting plaintext block number N, it XORs it with the previous ciphertext block (number N-1).
When decrypting, after decrypting ciphertext block N, it XORs the decrypted (but still XORed) result with the previous ciphertext block (number N-1) to recover the original plaintext block N.
For the very first block, since there is no "previous" block to use, CBC cryptosystems generate a random initial block called an [_Initialization Vector_ (IV)](https://en.wikipedia.org/wiki/Initialization_vector).
The IV is used to XOR the first block of plaintext, and is transmitted along with the message (often prepended to it).
This means that if you encrypt one block of plaintext in CBC mode, you might get _two_ blocks of "ciphertext": the IV, and your single block of actual ciphertext.

All this means that, when you change any part of the plaintext, those changes will propagate through to all subsequent ciphertext blocks because of the XOR-based chaining, preserving ciphertext indistinguishability for those blocks.
That will stop you from carrying out the chosen-plaintext prefix attacks from the last few challenges.
Moreover, every time you re-encrypt, even with the same key, a new (random) IV will be used, which will propagate changes to all of the blocks anyways, which means that even your sampling-based CPA attacks from the even earlier levels will not work, either.

Sounds pretty good, right?
The only relevant _disadvantage_ that CBC has over EBC is that encryption has to happen sequentially.
With ECB, you could encrypt, say, only the last part of the message if that's all you have to send.
With CBC, you must encrypt the message from the beginning.
In practice, this does not tend to be a problem, and ECB should never be used over CBC.

This level is just a quick look at CBC.
We'll encrypt the flag with CBC mode.
Go and decrypt it!
