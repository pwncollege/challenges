ASCII and UTF-8 are encodings meant for very specific data: text (or text-like characters).
Hex encoding is more general, and you can apply it to any data.
The reason that we might use an encoding like hex is to transfer information via some medium where it is hard to write arbitrary binary code, such as a piece of paper or certain communication protocols.
However, it is horribly inefficient: it _doubles_ the size of the data by outputting two ASCII hex digits for every byte!

Hex is inefficient for a similar reason that it convenient: there are only 4 bits available per digit, and since each output character digit takes 8 bits to display (in ASCII), the data size doubles.
Luckily, we can increase the efficiency of an encoding by increasing the number of bits we can convey per output character.

The name "base64" comes from the fact that there are 64 characters used in each output character.
These can actually vary, but the standard base64 encoding uses an "alphabet" of the uppercase letters `A` through `Z`, the lowercase letters `a` through `z`, the digits `0` through `9`, and the `+` and `/` symbols.
This results in 64 total output symbols, and each symbol can encode `2**6` (2 to the power of 6) possible input symbols, or 6 bits of data.
That means that to encode a single byte (8 bits) of input, you need more than one base64 output character.
In fact, you need _two_: one that encodes the first 6 bits and one that encodes the remaining 2 (with 4 bits of that second output character being unused).
To mark these unused bits, base64 encoded data appends an `=` for every two unused bits.
For example:

```console
hacker@dojo:~$ echo -n A | base64
QQ==
hacker@dojo:~$ echo -n AA | base64
QUE=
hacker@dojo:~$ echo -n AAA | base64
QUFB
hacker@dojo:~$ echo -n AAAA | base64
QUFBQQ==
hacker@dojo:~$
```

As you can see, 3 bytes (`3*8 == 24` bits) encode precisely into 4 base64 characters (`4*6 == 24` bits).

base64 is a popular encoding because it can represent any data without using "tricky" characters such as newlines, spaces, quotes, semicolons, unprintable special characters, and so on.
Such characters can cause trouble in certain scenarios, and base64-encoding the data avoids this nicely.

You've also explored other "base" encodings: base2 is binary, and base16 is hex!

Now, go and decode your way to the flag!

----
**HINT:**
You can use Python's `base64` module (note: the base64 decoding functions in this module consume and return Python bytes) or the `base64` command line utility to do this!

**FUN FACT:**
The flag data in `pwn.college{FLAG}` is actually base64-encoded ciphertext.
You're well on the way to being able to build something like the dojo!
