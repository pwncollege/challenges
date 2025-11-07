Now, let's talk about `str`ings!
In Python, strings are meant for human consumption.
A string is a sequence of characters that a human might write down, read, speak, and dream.
This includes things like letters of the alphabet but also things like 🕴️.
When one thinks about how many different letters of different alphabets and different emoji and so on there are, it's clear that there are _thousands_ of different options for each character of a string.

The representation of a human-readable character as a bunch of bytes in memory is yet another _Encoding_ (here, used as a noun).
A character, such as 🐉, is "encoded" (here, used as a verb) by bytes in memory, and those bytes "decode" to that character.
In this use of "encoding" and "decoding", the data actually stays the same, but its interpretation changes: the encoding is applied by, say, your commandline terminal to translate the bytes being sent by the program into the characters and emoji you see on the screen.

In Python, you convert a `str` to its equivalent `bytes` by doing `my_string.encode()`.
If you have a bunch of bytes that you want to interpret as a string, you can do `my_bytes.decode()`.
But how are string characters mapped to byte values?

Back in its early days (say, pre-2000), when computing was less international and people still typed `:-)` instead of 🙂, people didn't really worry about the limited number of characters that a single byte could represent.
Thus, early encodings simply encoded each character to be a single byte, with a resulting limit of 256 possible characters.
Because early computing was predominantly US- and Western Europe-based, the most popular such encoding, specifically designed to represent characters in the Latin alphabet with various byte values, was [_ASCII_](https://en.wikipedia.org/wiki/ASCII), dating back to 1963 (ancient history by computing standards!).

ASCII is pretty simple: every character is one byte, uppercase letters are `0x40+letter_index` (e.g., A is `0x41`, F is `0x46`, and Z is `0x5a`), lowercase letters are `0x60+letter_index` (a is `0x61`, f is `0x66`, and z is `0x7a`), and numbers (yes, the numeric characters you're seeing are _not_ bytes of those values, they are ASCII-encoded number characters) are `0x30+number`, so 0 is `0x30` and 7 is `0x37`.
Useful special characters are sprinkled around the mapping as well: forward slash (`/` is `0x2f`), space is `0x20`, and newline is `0x0a`.
Because early computing pioneers were making stuff up as they went along, some of the ASCII characters aren't really characters: `0x07` is a _bell_; it literally makes your terminal beep when it is "printed" out!
Other "control characters" do other whacky things: `0x08`, for example, _deletes the last character_ on the terminal instead of being a character itself.

Byte values below `0x80` (`128`), considered "standard ASCII", were pretty universally defined even for non-English countries.
You can see this whole standard ASCII definition with `man ascii`!
You can also use standard ASCII in python to encode strings: `my_string.encode("ascii")`.
But beware, standard ASCII doesn't define values above `0x80`, so if you _decode_ bytes that have those values, you will get an exception!
This, for example, won't work: `b"\x80".decode("ascii")`.

Values _above_ `0x80` ("extended ASCII") were used by different countries for their own characters, leading to some chaos due to colliding byte values.
In the US, the typical "extended ASCII" encoding was called [Latin 1](https://en.wikipedia.org/wiki/ISO/IEC_8859-1), and it defined a character for each of the 256 possible byte values.
This is useful for us because we can use "latin1" to easily convert between Python's bytes and strings, including: `b"\x80".decode("latin1")`.

In this challenge, we want you to give us ASCII-encoded hex values (fun fact: specifying byte values in hexadecimal is called "hex encoding"!), and we'll match them against the password.
Good luck!

---
**NOTE:**
As you read the challenge to understand what value you need to send, you'll notice that some parts of the `bytes` constant specified for `correct_password` looks ... weird.
Each byte in `correct_password` represents a byte in memory, but they often still have useful, human-relevant information.
Printing _every_ byte with escape sequences, though it would be valid, would not be as useful for humans, even if bytes aren't _really_ meant for human consumption.
Thus, the Python developers decided to represent bytes as ... standard ASCII!
Python `bytes` are specified using ASCII characters, with the weirder "non-printable" ones (e.g., anything over `0x80` and a few others are specified using `\x` _escape sequences_).
This can work for normal characters as well: `\x41` happily encodes `A`.
Some other special characters have their own bespoke escape sequences: for example, `\n` encodes a newline character (equivalent to `\x0a`).
You can see other escape sequences in `man ascii`.
Because `\` is used as an escape sequence, Python (and other languages that use the escape sequence concept, which is almost everything) must specify an _actual_ backslash as an escape sequence as well (specifically, `\\` encodes a `\` byte with a value of `0x5c`).

Okay, that was a lot.
Go put it into practice!
