One byte at a time, in the 8-bit register `al`:

```
mov al, [rdi+0]
cmp al, 0x41
jne fail
```

And here's the payoff. A single byte has no order to reverse, so the immediates *are* the characters, already in order --- `0x41` is just `'A'`. Sixteen byte-compares, and no endian-correcting at all.

This is the far end of the rule you've been applying: the reversal unit is the read size, so a one-byte read reverses nothing.
Read the immediates straight down the disassembly and run it.

```console
hacker@dojo:~$ objdump -d -M intel /challenge/reverse-me
hacker@dojo:~$ /challenge/reverse-me YOUR_PASSWORD_HERE
```

----
**WARNING**:
`/challenge/reverse-me` is a **SUID** binary, so debugging it drops its privileges and the `open("/flag")` inside will silently fail under gdb.
Use `objdump` to read it, but run it **directly** to get the flag.
