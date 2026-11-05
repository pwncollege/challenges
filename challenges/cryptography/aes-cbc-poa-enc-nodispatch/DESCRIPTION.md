Now, you've previously started from a single valid input (the encrypted `sleep` command).
What if you have _zero_ valid inputs?
Turns out that all this still works!

Why?
Random data decrypts to ... some other random data.
Likely, this has a padding error.
You can control the IV just like before to figure out the right 16th byte to xor in to resolve that padding error, and now you have a ciphertext that represents a 15-byte random message.
For you, there's no real difference between that random message and `sleep`: the attack is the same!

Go try this now.
No dispatcher, just you and the flag.
