You have seen that `byte`, `word`, `dword`, and `qword` describe how many bytes an instruction reads or writes.
When an unsigned value moves from a smaller size to a larger one, its value must stay the same.
The new high bits are therefore filled with zeroes: the byte `0xff` becomes the 64-bit value `0x00000000000000ff`, which is still `255`.

This is called **zero extension**.
On x86-64, `movzx` moves a smaller source into a larger destination and fills the new high bits with zeroes.
The form you need here is:

```asm
movzx rax, BYTE PTR [rdi]
```

Write a function called `solve` that takes a pointer to one unsigned byte in `rdi`.
Load that byte, zero-extend it to 64 bits, return it in `rax`, and export it with `.global solve`.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```
