Endianness isn't special to 64-bit values.
_Every_ integer read from memory comes back little-endian, and the bytes that get reversed are exactly the ones covered by that read.
For example, consider the following bytes, contiguously chilling in memory pointed to by `rdi`:

```
rdi -> 11 22 33 44 55 66 77 88
```

If you read all 8 bytes into, say, `rsi` with `mov rsi, [rdi]`, `rsi` will have the value of `0x8877665544332211`.
You could also read it as two 32-bit (4 byte) values (into, say, the 4-byte _partial_ registers `esi` and `edx`, which are 32 bits of `rsi` and `rdx`, respectively):

```
mov esi, [rdi]      // results in 0x44332211 in esi
mov edx, [rdi+4]    // results in 0x88776655 in edx
```

This makes sense written out, but it _can_ confuse some people.
Specifically, what does _not_ happen is the reversal of the whole 8-byte value (in which case, `esi` above would have the 0x88).

You'll practice this in this challenge.
`/challenge/reverse-me` checks the same kind of password four bytes at a time, as **32-bit values** (termed "dwords"), so you get four integers instead of two.
Each dword still reverses its own four bytes; the dwords themselves stay in address order, just like the qwords did.
Because a dword fits the normal immediate size, each check is a direct `cmp eax, 0x........` --- the value to recover is right there in the instruction:

```
mov eax, [rdi+0]
cmp eax, 0x44434241
jne fail
```

Disassemble `/challenge/reverse-me`, read the four `cmp eax` immediates, endian-correct each dword, concatenate them in address order, and run it with the result:

```console
hacker@dojo:~$ objdump -d -M intel /challenge/reverse-me
hacker@dojo:~$ /challenge/reverse-me YOUR_PASSWORD_HERE
```

----
**WARNING**:
`/challenge/reverse-me` is a **SUID** binary, so debugging it drops its privileges and the `open("/flag")` inside will silently fail under gdb.
Use `objdump` to read it, but run it **directly** to get the flag.
