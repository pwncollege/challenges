Let's put the last two challenges together.
The previous challenges had just one ciphertext block, whether it started like that or you quickly got there by discarding the all-padding block.
Thus, you were able to mess with that block's plaintext by chaining up the IV.

This level encrypts the actual flag, and thus has multiple blocks that actually have data.
Keep in mind that to mess with the decryption of block N, you must modify ciphertext N-1.
For the first block, this is the IV, but not for the rest!

This is one of the hardest challenges in this module, but you can get your head around if you take it step by step.
So, what are you waiting for?
Go recover the flag!
