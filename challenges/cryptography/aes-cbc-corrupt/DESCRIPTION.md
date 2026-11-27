CBC-based cryptosystems XOR the previous block's *ciphertext* to recover the plaintext of a block after decryption.
This done for many reasons, including:

1. This XOR is what separates it from ECB mode, and we've seen how fallible ECB is.
2. If it XORed the _plaintext_ of the previous block instead of the ciphertext, the efficacy would be dependent on the plaintext itself (for example, if the plaintext was all null bytes, the XOR would have no effect). Aside from reducing the chaining effectiveness, this could leak information about the plaintext (big no no in cryptosystems)!
3. If it XORed the plaintext of the previous block instead of the ciphertext, the "random access" property of CBC, where the recipient of a message can decrypt starting from any block, would be lost. The recipient would have to recover the previous plaintext, for which they would have to recover the one before that, and so on all the way to the IV.

Unfortunately, in situations where the message could be modified in transit (think: Intercepting Communications), a crafty attacker could directly influence the resulting decrypted plaintext of block N by XORing carefully-chosen values into the ciphertext of block N-1.
This would corrupt block N-1 (because it would decrypt to garbage), but depending on the specific situation, this might be acceptable.
Moreover, doing this to the IV allows the attacker to XOR the plaintext of the first block without corrupting any block!

In security terms, CBC preserves (imperfectly, as we'll see in the next few challenges) Confidentiality, but does not preserve Integrity: the messages can be tampered with by an attacker!

We will explore this concept in this level, where a task dispatcher will dispatch encrypted tasks to a task worker.
Can you force a flag disclosure?
