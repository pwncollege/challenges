Strangely enough, we'll start our crypto journey with the humble [Exclusive Or](https://en.wikipedia.org/wiki/Exclusive_or) (XOR) operator.
An XOR is one of the most common [bitwise operators](https://en.wikipedia.org/wiki/Logical_connective) that you will encounter in your security journey, _especially_ in cryptography.
A couple of terms to unpack here...

**Bitwise.**
Remember from [Dealing with Data](/fundamentals/data-dealings/) that computers think in binary!
That is, they conceptualize numbers in [base 2](https://www.google.com/search?q=learn+number+bases), so something like `9` is expressed as `1001`.
An XOR operates on one pair of bits at a time, resulting in in `1` if the bits are different (one is `1` and the other is `0`) or `0` if they are the same (both `1` or both `0`).
It is then applied to every bit pair independently, and the results are concatenated.
For example, decimal `9` (`1001`) XORed with decimal `5` (`0101`) results in `1100` (decimal 12).

**Cryptography.**
Why is XOR so common in crypto?
In cryptography, it is common because it is [_self-inverse_](https://en.wikipedia.org/wiki/Exclusive_or#Properties)!
That is (using `^` for XOR here, which is consistent with many programming languages), `5 ^ 9 == 12`, and `12 ^ 9 == 5`.
If the number `9` is a key only known to you and me, I can send you messages by XORing them with `9`, and you can recover the message with XORing them with `9` as well!
Obviously, we can achieve this property with me adding 9 and you subtracting 9, without using XOR, but this requires more complex circuitry and extra bits (e.g., to handle "carrying the 1" in `1111 + 0001 == 10000`), whereas XOR does not have this problem (`1111 ^ 0001 == 1110`).

In this level, you will learn to XOR!
We'll give you a shared _key_, `XOR` a secret number with it, and expect you to recover the number.

----
**HINT:** Use Python's `^` operator to XOR integers!
