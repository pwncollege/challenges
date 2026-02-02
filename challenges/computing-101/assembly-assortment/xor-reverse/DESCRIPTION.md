This challenge introduces a new type of operation: **bitwise XOR**.
Unlike `add` and `sub`, which do arithmetic, `xor` operates on individual bits.

The `xor` instruction computes the _exclusive or_ of two values: for each bit position, the result is `1` if exactly one of the two input bits is `1`, and `0` otherwise.
For example:

```
  01100001  (0x61, 'a')
^ 00101010  (0x2a, 42)
---------
  01001011  (0x4b, 75)
```

The syntax is the same as `add` and `sub`: `xor rax, 42`.

A key property of XOR is that it's **its own inverse**: `xor`ing a value with the same value twice gives back the original value.
So if you see:

```
xor    BYTE PTR [rax],0x2a
cmp    BYTE PTR [rax],0x4b
```

The program XORs your input byte with `0x2a` and checks if the result is `0x4b`.
To reverse this, XOR the target with the key: `0x4b ^ 0x2a = 0x61`, which is `'a'`.

Now: disassemble the binary, reverse the XOR, and get the flag!
