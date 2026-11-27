Much of the field of Cryptography deals with encrypting _text_.
This text, as you might (again!) recall from [Dealing with Data](/fundamentals/data-dealings) is mapped to specific byte values, as specified by an encoding standard, such as ASCII or UTF-8.
Here, we'll stick to ASCII, though the concepts apply identically to other encodings.

The cool thing is that, since ASCII puts byte values to characters, we can do operations like XOR!
This has obvious implications for cryptography.

In this level, we'll explore these implications byte by byte.
The challenge will give you one letter a time, along with a key to "decrypt" (XOR) the letter with.
You give us the result of the XOR.
For example:

```console
hacker@dojo:~$ /challenge/run
Challenge number 0...
- Encrypted Character: A
- XOR Key: 0x01
- Decrypted Character?
```

How would you approach this?
You can `man ascii` and find the entry for A:

```none
Oct   Dec   Hex   Char
──────────────────────
101   65    41    A
```

So A is `0x41` in hex.
You would XOR that with `0x01`
The result here would be: `0x41 ^ 0x01 == 0x40`, and, according to `man ascii`:

```none
Oct   Dec   Hex   Char
──────────────────────
100   64    40    @
```

It's the @ character!

```console
hacker@dojo:~$ /challenge/run
Challenge number 0...
- Encrypted Character: A
- XOR Key: 0x01
- Decrypted Character? @
Correct! Moving on.
```

Now it's your turn!
Can you XOR things up and get the flag?
