For historical reasons, different encodings tend to gain traction in different contexts.
For example, on the web, the standard way to encode binary data is base64, an encoding that you learned in [Dealing with Data](/fundamentals/data-dealings).
Channel this skill now, adapting your previous solution for base64!

You'll (re-)note that base64 isn't as convenient to reason about as hex.
Why do people use it?
One reason: every byte requires _two_ hex letters to encode, whereas base64 encodes every 3 bytes with 4 letters.
This means that, when sending each letter as a byte itself over the network, for example, base64 is marginally more efficient.
On the other hand, it's a headache to work with, because of the unclean bit boundaries!

Throughout the rest of the modules, challenges might use hex or base64, as our heart desires.
It's important to be able to handle either!
