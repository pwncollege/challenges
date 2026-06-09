You've seen that a multi-byte value sits in memory low byte first, so reading one back into a register reverses its bytes.
A single register tops out at eight bytes, but plenty of values are wider than that (and wider than the CPU can easily access at one time).

Depending on the program, such values might be accessed sequentially, register-width by register-width.
For example, consider a 16-byte password, as you will experience in this challenge.
The sixteen ASCII bytes, read as two 8-byte qwords, might be accessed like this:

| Address     | Value  |
|-------------|--------|
| `0x1337000` | `0x41` |
| `0x1337001` | `0x42` |
| `0x1337002` | `0x43` |
| `0x1337003` | `0x44` |
| `0x1337004` | `0x45` |
| `0x1337005` | `0x46` |
| `0x1337006` | `0x47` |
| `0x1337007` | `0x48` |
| `0x1337008` | `0x49` |
| `0x1337009` | `0x4a` |
| `0x133700a` | `0x4b` |
| `0x133700b` | `0x4c` |
| `0x133700c` | `0x4d` |
| `0x133700d` | `0x4e` |
| `0x133700e` | `0x4f` |
| `0x133700f` | `0x50` |

As a string value stored in memory byte by byte, that ordering is *not* affected by endianness.
What endianness flips is the bytes _as they end up in a register after the `mov`_: each one, being a multi-byte value, still reads back low byte first.
So if `rdi` is pointing to this buffer, a `mov rsi, [rdi]` would end up with the value `0x4847464544434241`, and the next `mov rsi, [rdi+8]` would have the value `0x504f4e4d4c4b4a49`.

So to rebuild a longer value: keep the qwords in the order you get them, but reverse the bytes inside each one.

Disassemble `/challenge/reverse-me`, read the two qword values it checks your input against, endian-correct each one, concatenate them in order, and run it with the result:

```console
hacker@dojo:~$ objdump -d -M intel /challenge/reverse-me
hacker@dojo:~$ /challenge/reverse-me YOUR_PASSWORD_HERE
```

----
**WARNING**:
`/challenge/reverse-me` is a **SUID** binary, so debugging it drops its privileges and the `open("/flag")` inside will silently fail under gdb.
Use `objdump` to read it, but run it **directly** to get the flag.
