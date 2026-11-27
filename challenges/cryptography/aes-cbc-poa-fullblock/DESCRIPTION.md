The previous challenge had you decrypting a partial block by abusing the padding at the end.
But what happens if the block is "full", as in, 16-bytes long?
Let's explore an example with the plaintext `AAAABBBBCCCCDDDD`, which is 16 bytes long!
As you recall, PKCS7 adds a whole block of padding in this scenario!
What we would see after padding is:

| Plaintext Block 1  | Plaintext Block 2 (oops, just padding!)                            |
|--------------------|--------------------------------------------------------------------|
| `AAAABBBBCCCCDDDD` | `\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10` |

When encrypted, we'd end up with three blocks:

| Ciphertext Block 1 | Ciphertext Block 2 | Ciphertext Block 3 |
|--------------------|--------------------|--------------------|
| IV | Encrypted `AAAABBBBCCCCDDDD` | Encrypted Padding |

If you know that the plaintext length is aligned to the block length like in the above example, you already know the plaintext of the last block (it's just the padding!).
Once you know it's all just padding, you can discard it and start attacking the next-to-last block (in this example, Ciphertext Block 2)!
You'd try tampering with the last byte of the plaintext (by messing with the IV that gets XORed into it) until you got a successful padding, then use that to recover (and be able to control) the last byte, then go from there.
The same POA attack, but against the _second-to-last_ block when the last block is all padding!
