In the last level, you reached rightward into your caller's frame.
Now you'll look leftward, at bytes left behind by a function that already returned.

When your code calls a function, that callee can move `rsp` left and use stack memory of its own.
When it returns, it moves `rsp` back right, but the bytes it wrote are not automatically erased.
They become stale stack data: ordinary memory left behind by code that already finished.
Software could erase those bytes before returning, but erasing data means running more instructions and writing more memory.
When the leftover data is sensitive, skipping that erasure can become a vulnerability.
This level starts with the smallest version of that issue: one stale 8-byte value.

This challenge passes your `solve` a function pointer named `load_secret`.
Call it first.
It stores one 8-byte secret in its own stack frame and returns, leaving those bytes at a negative offset from your current `rsp`.
The checker will tell you the exact offset.

Because the goal is to return the 8-byte value itself, load it with `mov`:

```asm
mov rax, qword ptr [rsp-0x40]
```

That example offset is hypothetical; use the offset printed by the checker.
Write a function called `solve` that calls `load_secret`, loads the stale 8-byte value into `rax`, and returns.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```

For debugging a submitted function inside a shared library, refer back to [Writing From a Shared Library](/computing-101/control-flow/callee-write).
