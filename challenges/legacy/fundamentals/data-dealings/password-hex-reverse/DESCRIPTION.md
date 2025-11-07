So far, we have seen a few types of encodings: UTF-8, UTF-16, extended ASCII (latin-1), and hex encoding.
This encoding translates data, whether that's a concept such as a 🎈 emoji character or an actual byte in memory into other bytes.
What happens when you mess with the encoded data?
Nothing good!
In UTF-8, 🎈 encodes to:

```console
hacker@dojo:~$ ipython
In [1]: "🎈".encode("utf-8")
Out[1]: b'\xf0\x9f\x8e\x88'
```

If we mess with the resulting bytes, and then decode them, we would (of course) get something different:

```console
In [2]: b'\xf0\x9f\x8e\xaa'.decode("utf-8")
Out[2]: '🎪'

In [3]: b'\xf0\x9f\x8e\x42'.decode("utf-8")
---------------------------------------------------------------------------
UnicodeDecodeError                        Traceback (most recent call last)
Cell In[3], line 1
----> 1 b'\xf0\x9f\x8e\x42'.decode("utf-8")

UnicodeDecodeError: 'utf-8' codec can't decode bytes in position 0-2: invalid continuation byte
```

The first modification resulted in a different emoji, and the second one errored out.
Depending on the encoding, not all byte values can be decoded properly!
For UTF-8, this is due to a complex algorithm to specify the data.
For hex encoding, this is due to only numbers 0 through 9 and letters A through F being valid in hexadecimal!

All this being said, any encoding _can_ be messed with to some extent, as we can see in the first example above.
When a security flaw allows data to be corrupted, this can enable an attacker to carefully transform data to their purposes.
We'll learn about how to protect data from this later in pwn.college, but for now, let's practice this concept by seeing what happens when we mess with some hex!
