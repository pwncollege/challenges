You just read how x86 stores multi-byte values *little-endian* --- low byte first.
Time to use it: `/challenge/reverse-me` hides an 8-character password in a single qword, deep in its own code.

It loads your input and compares all 8 bytes at once against a hard-coded value:

```
movabs rbx, 0x4847464544434241
mov    rax, [rdi]
cmp    rax, rbx
jne    fail
```

(`movabs` is new, but it's just a `mov`: a normal `mov`'s immediate maxes out at 32 bits, so the assembler uses this wider form --- "move absolute" --- when the constant fills all 64. Read it as a `mov`.)

That immediate is the password *as the CPU read it from memory* --- little-endian, so its bytes are the characters in reverse:

```
0x4847464544434241  ->  bytes 48 47 46 45 44 43 42 41  (high to low, as printed)
                    ->  low byte first: 41 42 43 44 45 46 47 48  ->  "ABCDEFGH"
```

Disassemble it, read that one `movabs` immediate, reverse its eight bytes into the password, and run it:

```console
hacker@dojo:~$ objdump -d -M intel /challenge/reverse-me
hacker@dojo:~$ /challenge/reverse-me YOUR_PASSWORD_HERE
```

----
**WARNING**:
`/challenge/reverse-me` is a **SUID** binary, so debugging it drops its privileges and the `open("/flag")` inside will silently fail under gdb.
Use `objdump` to read it, but run it **directly** to get the flag.
