In this challenge you will decrypt a secret encrypted with a [one-time pad](https://en.wikipedia.org/wiki/One-time_pad).
Although simple, this is the most secure encryption mechanism, if a) you can securely transfer the key and b) you only ever use the pad _once_.
It's also the most simple encryption mechanism: you simply _XOR_ the bits of the plaintext with the bits of the key one by one!

This challenge encrypts the flag with a one-time pad and then gives you the key.
Luckily, a one-time pad is a _symmetric_ cryptosystem: that is, you use the same key to encrypt and to decrypt, so you have everything you need to decrypt the flag!

----
**Fun fact:** the One-time Pad is the _only_ cryptosystem that humanity has been able to _prove_ is perfectly secure.
If you securely transfer the key, and you only use it for one message, it cannot be cracked even by attackers with infinite computational power!
We have not been able to make this proof for any other cryptosystem.
