So you can manipulate the padding...
If you messed up somewhere along the lines of the previous challenge and created an invalid padding, you might have noticed that the worker _crashed_ with an error about the padding being incorrect!

It turns out that this one crash _completely_ breaks the Confidentiality of the AES-CBC cryptosystem, allowing attackers to decrypt messages without having the key.
Let's dig in...

Recall that PKCS7 padding adds N bytes with the value N, so if 11 bytes of padding were added, they have the value `0x0b`.
During unpadding, PKCS7 will read the value N of the last byte, make sure that the last N bytes (including that last byte) have that same value, and remove those bytes.
If the value N is bigger than the block size, or the bytes don't all have the value N, most implementations of PKCS7, including the one provided by PyCryptoDome, will error.

Consider how careful you had to be in the previous level with the padding, and how this required you to know the letter you wanted to remove.
What if you didn't know that letter?
Your random guesses at what to XOR it with would cause an error 255 times out of 256 (as long as you handled the rest of the padding properly, of course), and the one time it did not, by known what the final padding had to be and what your XOR value was, you can recover the letter value!
This is called a [_Padding Oracle Attack_](https://en.wikipedia.org/wiki/Padding_oracle_attack), after the "oracle" (error) that tells you if your padding was correct!

Of course, once you remove (and learn) the last byte of the plaintext, the second-to-last byte becomes the last byte, and you can attack it!

So, what are you waiting for?
Go recover the flag!

----
**FUN FACT:**
The only way to prevent a Padding Oracle Attack is to avoid having a Padding Oracle.
Depending on the application, this can be surprisingly tricky: a failure state is hard to mask completely from the user/attacker of the application, and for some applications, the padding failure is the only source of an error state!
Moreover, even if the error itself is hidden from the user/attacker, it's often _inferable_ indirectly (e.g., by detecting timing differences between the padding error and padding success cases).

**RESOURCES:**
You might find some animated/interactive POA demonstrations useful:

- [An Animated Primer from CryptoPals](https://www.nccgroup.com/us/research-blog/cryptopals-exploiting-cbc-padding-oracles/)
- [Another Animated Primer](https://dylanpindur.com/blog/padding-oracles-an-animated-primer/)
- [An Interactive POA Explorer](https://paddingoracle.github.io/)
