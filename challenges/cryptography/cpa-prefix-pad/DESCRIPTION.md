The previous challenge ignored something very important: [_padding_](https://en.wikipedia.org/wiki/Padding_(cryptography)#Byte_padding).
AES has a 128-bit (16 byte) block size.
This means that input to the algorithm _must_ be 16 bytes long, and any input shorter than that must be _padded_ to 16 bytes by having data added to the plaintext before encryption.
When the ciphertext is decrypted, the result must be _unpadded_ (e.g., the added padding bytes must be removed) to recover the original plaintext.

_How_ to pad is an interesting question.
For example, you could pad with null bytes (`0x00`).
But what if your data has null bytes at the end?
They might be erroneously removed during unpadding, leaving you with a plaintext different than your original!
This would not be good.

One padding standard (and likely the most popular) is PKCS7, which simply pads the input with bytes all containing a value equal to the number of bytes padded.
If one byte is added to a 15-byte input, it contains the value `0x01`, two bytes added to a 14-byte input would be `0x02 0x02`, and the 15 bytes added to a 1-byte input would all have a value `0x0f`.
During unpadding, PKCS7 looks at the value of the last byte of the block and removes that many bytes.
Simple!

But wait...
What if exactly 16 bytes of plaintext are encrypted (e.g., no padding needed), but the plaintext byte has a value of `0x01`?
Left to its own devices, PKCS7 would chop off that byte during unpadding, leaving us with a corrupted plaintext.
The solution to this is slightly silly: if the last block of the plaintext is exactly 16 bytes, we add a block of _all_ padding (e.g., 16 padding bytes, each with a value of `0x10`).
PKCS7 removes the whole block during unpadding, and the sanctity of the plaintext is preserved at the expense of a bit more data.

Anyways, the previous challenge explicitly disabled this last case, which would have the result of popping in a "decoy" ciphertext block full of padding as you tried to push the very first suffix byte to its own block.
This challenge pads properly.
Watch out for that "decoy" block, and go solve it!

----
**NOTE:**
The full-padding block will *only* appear when the last block of plaintext perfectly fills 16 bytes.
It'll vanish when one more byte is appended (replaced with the padded new block containing the last byte of plaintext), but will reappear when the new block reaches 16 bytes in length.
