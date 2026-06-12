You have seen that `byte`, `word`, `dword`, and `qword` describe how many bytes an instruction reads or writes.
Now add one more wrinkle: a smaller value can be copied into a larger register as either unsigned or signed.

If the byte is unsigned, filling the high bytes with zero is fine: `0x7f` becomes `0x000000000000007f`.
But a signed byte uses two's complement.
The byte `0xff` is `-1`, so extending it to 64 bits must fill the new high bits with `1`s: `0xffffffffffffffff`.

That is **sign extension**.
It copies the sign bit, not zeroes, into the new high bits.
On x86-64, the form you need here is:

```asm
movsx rax, BYTE PTR [rdi]
```

This reads one byte from the address in `rdi`, treats that byte as signed, and returns the 64-bit signed value in `rax`.

Write a function called `solve` that takes a pointer to one byte in `rdi`.
Load that byte as a signed 8-bit value, sign-extend it to 64 bits, return it in `rax`, and export it with `.global solve`.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```
