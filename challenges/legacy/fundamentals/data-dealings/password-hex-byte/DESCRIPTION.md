Now, life must get complex.
You may have noticed the `b` letters in front of the password constants throughout this module.
Python has two types of string-like constants: `str`ings (specified as `"asdf"`) and `bytes` (specified as `b"asdf"`).
Let's talk about `bytes` in this level.

Bytes are what is actually stored in your computer's memory.
As you might know, computers think in binary: just a bunch of ones and zeroes.
For historical reasons, we express these ones and zeroes ("bits") in groups of 8, and each group of 8 (a "byte").
This number is purely arbitrary: early computers (pre-1960s or so) didn't have this grouping at all, or had other arbitrary groupings.
It is very feasible for there to be an alternate universe in which a byte is 16, 32, or really any numbers of bits (though for math reasons, it'll likely remain a power-of-2).

A single binary digit (bit) can represent two values (`0` and `1`), two bits can represent four values (`00`, `01`, `10`, and `11`), three bits can represent eight values (`000`, `001`, `010`, `011`, `100`, `101`, `110`, `111`), and four bits can represent sixteen values.
Comparatively, a single decimal digit can represent 10 values (from `0` to `9`).
Ten values are represented by roughly `log2(10) == 3.3219...` bits, and you get weird situations like binary `1001` being decimal `9`, but binary `1100` (still 4 binary digits) being `12` (_two_ decimal digits!).
Another way of expressing this digit desynchronization between decimal and binary is that decimal does not have clean _bit boundaries_.

The lack of bit boundaries makes reasoning about the relationship between decimal and binary complex.
For example, it is hard to spot-translate numbers between decimal and binary in general: we can work out that `97` is `110001`, but it's hard to see that at a glance.

It's much easier to spot-translate between bases that have more alignment between digits.
For example, a single hexadecimal (base 16) digit can represent 16 values (`0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `a`, `b`, `c`, `d`, `e`, `f`): the same number of values that binary can represent in 4 digits!
This allows us to have a super simple mapping:

| Hex | Binary | Decimal |
|-----|--------|---------|
| `0` | `0000` | `0`     |
| `1` | `0001` | `1`     |
| `2` | `0010` | `2`     |
| `3` | `0011` | `3`     |
| `4` | `0100` | `4`     |
| `5` | `0101` | `5`     |
| `6` | `0110` | `6`     |
| `7` | `0111` | `7`     |
| `8` | `1000` | `8`     |
| `9` | `1001` | `9`     |
| `a` | `1010` | `10`    |
| `b` | `1011` | `11`    |
| `c` | `1100` | `12`    |
| `d` | `1101` | `13`    |
| `e` | `1110` | `14`    |
| `f` | `1111` | `15`    |

This mapping from a hex digit to 4 bits is something that's easily memorizable (most important: memorize `1`, `2`, `4`, and `8`, and you can quickly derive the rest).
Better yet, two hex digits is **8** bits, which is one byte!
Unlike decimal, where you'd have to memorize 16 mappings for 4 bits and 256 mappings for 8 bits, with hexadecimal, you only have to memorize 16 mappings for 4 bits and the same amount of mappings for 8 bits, since it's just two hexadecimal digits concatenated!
Some examples:

| Hex  | Binary      | Decimal |
|------|-------------|---------|
| `00` | `0000 0000` | `0`     |
| `0e` | `0000 1110` | `14`    |
| `3e` | `0011 1110` | `62`    |
| `e3` | `1110 0011` | `227`   |
| `ee` | `1110 1110` | `238`   |

Now you're starting to see the beauty.
This gets even more obvious when you expand beyond one byte of input, but we'll let you find that out through future challenges!

Now, let's talk about notation.
How do you differentiate `11` in decimal, `11` in binary (which equals `3` in decimal), and `11` in hex (which equals `17` in decimal)?
For numerical constants, Python's notation is to prepend binary data with `0b`, hexadecimal with `0x`, and keep decimal as is, resulting in `11 == 0b1011 == 0xb`, `3 == 0b11 == 0x3`, and `17 == 0b10001 == 0x11`.
But for `bytes`, as in this challenge, you can specify them using _escape sequences_.
The escape sequence starts with `\x` and is followed by two hex digits, resulting in a single byte with that value being put in the `bytes` constant!

Armed with this knowledge, go and hex the challenge and get the flag!

---
**Fun facts:**
Some other Pythonisms that might be useful:

- If you `print(n)` a number or convert it to a string with `str(n)`, the number will be represented in base 10.
- You can get a hexadecimal string representation of a number using `hex(n)`.
- You can get a binary string representation of a number using `bin(n)`.
- Converting a string to a number with `int(s)` will read it as a base 10 number by default.
- You can specify a different base to use with a second argument: `int(s, 16)` will interpret the string as hex, `int(s, 2)` will interpret it as binary.
- You can try to auto-identify the number base using `int(s, 0)`, which requires a prefix on the string (`0b` or binary, `0x` for hex, nothing for decimal).
