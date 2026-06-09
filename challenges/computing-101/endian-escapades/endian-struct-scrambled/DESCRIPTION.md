The last struct read its fields top to bottom, in memory order, so reading the disassembly straight down handed you the password already in order.
Nothing guarantees that.
A program can check a struct's fields in *any* order it likes --- the order the compares appear in the code has nothing to do with where those bytes live in memory.

This `/challenge/reverse-me` checks the same five fields, but *scrambled*:

```
mov    ax,  [rdi+12]              ; the +12 word might be checked first...
cmp    ax,  0x....
mov    al,  [rdi+15]              ; ...then a byte from the very end...
cmp    al,  0x..
movabs rbx, 0x................    ; ...then the +0 qword, and so on.
mov    rax, [rdi+0]
cmp    rax, rbx
```

So you can no longer read the password straight down the disassembly.
Recover each field's *value* exactly as before, but now also read its *offset* from the `[rdi+X]` load --- that offset is where the bytes belong.
Place each field at its offset, concatenate in offset order, and you have the password.

```console
hacker@dojo:~$ objdump -d -M intel /challenge/reverse-me
hacker@dojo:~$ /challenge/reverse-me YOUR_PASSWORD_HERE
```

----
**WARNING**:
`/challenge/reverse-me` is a **SUID** binary, so debugging it drops its privileges and the `open("/flag")` inside will silently fail under gdb.
Use `objdump` to read it, but run it **directly** to get the flag.
