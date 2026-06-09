Smaller still: `/challenge/reverse-me` now checks two bytes at a time, as **words**.

The rule never changes --- the bytes that reverse are exactly the ones in the read.
A word read swaps its two bytes; the words stay in address order.
(And a one-byte read has nothing to swap, which is why single bytes never need endian-correcting.)

Disassemble `/challenge/reverse-me`, read the eight `cmp ax, 0x....` immediates, swap each pair, keep the words in address order, and run it:

```console
hacker@dojo:~$ objdump -d -M intel /challenge/reverse-me
hacker@dojo:~$ /challenge/reverse-me YOUR_PASSWORD_HERE
```

----
**WARNING**:
`/challenge/reverse-me` is a **SUID** binary, so debugging it drops its privileges and the `open("/flag")` inside will silently fail under gdb.
Use `objdump` to read it, but run it **directly** to get the flag.
