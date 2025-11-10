Once computing went international and emojis were added, people needed to be able to use more than 256 possible characters at a time.
In the modern era, this has been largely solved by the [UTF-8](https://en.wikipedia.org/wiki/UTF-8) encoding.
UTF-8 is a specific multi-byte encoding of [Unicode](https://en.wikipedia.org/wiki/Unicode), a global standardized character set containing essentially all characters known to humanity, plus the fun emoji that you know and love.
There are many ways to encode Unicode, and UTF-8 is one of them.
Unicode (character set) is to UTF-8 (encoding) as English (character set) is to standard ASCII (encoding).

Conveniently, UTF-8 is backwards-compatible with standard ASCII (e.g., standard ASCII byte values represent the same character in UTF-8 as in ASCII), but in certain situations will use _more than one byte_ to represent a single character.
This allows UTF-8 to have essentially limitless character options (it can always interpret more bytes!): currently, it supports well over 1,000,000 characters!

UTF-8 is (by default) how Python's strings are specified, so you can do stuff like `my_string = "💥"`).
You can convert that into the actual byte representation (as it's stored in bytes in memory) by doing `my_string.encode("utf-8")` which, in the case of the emoji in question, results in the bytes `b'\xf0\x9f\x92\xa5'`.
Those four bytes represent that emoji in UTF-8.

In this challenge, you will learn to craft emoji bytes.
We want you to create raw bytes representing UTF-8 emoji, hex-encode them, and send those hex values to us.
Can you do it?

---
**DOJO NOTE:**
Due to a bug with unicode displays in the GUI Desktop terminal, we recommend that you use the VSCode Workspace for this challenge (and any other emoji-dependent challenges!).
