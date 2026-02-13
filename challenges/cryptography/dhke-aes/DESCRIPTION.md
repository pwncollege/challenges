You might have noticed that DH doesn't actually allow you to encrypt data directly: all it does is facilitate the generation of the same secret value for both Alice and Bob.
This value cannot be _chosen_, what Alice and Bob get for `s` is uniquely determined by the values of `a`, `b`, `p`, and `g`!

This single-secret nature isn't necessarily a drawback of DHKE.
That's just what it's for: letting you exchange a secret for further use.

So how do Alice and Bob actually exchange information using DHKE?
Well, the hint is in the name: Diffie-Hellman _Key Exchange_.
That secret value, of course, can be used as a key for, e.g., a symmetric cipher, and information can be encrypted with that cipher between Alice and Bob!

Armed with your knowledge of DHKE, you will now build your first cryptosystem that resembles something real!
You'll use DHKE to negotiate an AES key, and the challenge will use that key to encrypt the flag.
Decrypt it, and win!
