Real programs rarely read a buffer at one uniform size.
They read *structs*: a handful of fields of *different* sizes, laid out one after another in memory (in fact, _struct_ is _structure_ for short).

This `/challenge/reverse-me` treats your password as a struct.
You might not know the C programming language, but if you did, this is what the structure would be defined as:

```c
struct { uint64_t a; uint32_t b; uint16_t c; uint8_t d; uint8_t e; };
```

The disassembly loads each field at its own width and offset:

```
movabs rbx, 0x................   ; a: 8-byte field at +0
mov    rax, [rdi+0]
cmp    rax, rbx
mov    eax, [rdi+8]               ; b: 4-byte field at +8
cmp    eax, 0x........
mov    ax,  [rdi+12]              ; c: 2-byte field at +12
cmp    ax,  0x....
mov    al,  [rdi+14]              ; d: 1-byte field at +14
cmp    al,  0x..
mov    al,  [rdi+15]              ; e: 1-byte field at +15
cmp    al,  0x..
```

This is the whole module in one challenge.
For each field, read three things off the access: its *width* (from `rax`/`eax`/`ax`/`al`), its *offset* (`[rdi+X]`), and its *value* (endian-correct the immediate according to the field's width).
Reassemble the fields in offset order and you have the password.

```console
hacker@dojo:~$ objdump -d -M intel /challenge/reverse-me
hacker@dojo:~$ /challenge/reverse-me YOUR_PASSWORD_HERE
```

----
**WARNING**:
`/challenge/reverse-me` is a **SUID** binary, so debugging it drops its privileges and the `open("/flag")` inside will silently fail under gdb.
Use `objdump` to read it, but run it **directly** to get the flag.
