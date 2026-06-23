In the last level, you loaded one stale 8-byte value from an old callee frame.
Now you'll use the same stale-stack idea on a byte buffer.

This challenge passes your `solve` a pointer to a function named `read_flag`.
Call that function first.
It puts the flag in its own stack frame and returns.
After it returns, that old frame is to the left of your current `rsp`, and the **flag bytes are still there** until something overwrites them!

Write a function called `solve` that calls the function pointer in `rdi`, then writes the stale flag bytes from the old callee frame to stdout.
From `solve`'s perspective, those stale bytes sit at a negative offset from `rsp`; find the exact offset in `gdb` or read it from the checker output.
The important distinction is value versus address.
If you wanted to load one 8-byte value from that old frame, you would use `mov`:

```asm
mov rax, qword ptr [rsp-0x40]
```

But `write` needs the address of the first byte in `rsi`, not the qword stored there as a value.
For that, compute the address with `lea`:

```asm
lea rsi, [rsp-0x40]
```

That example offset is hypothetical; use the offset printed by the checker.
Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```

----

**DEBUGGING TIPS:**
For the general shared-library debugging workflow, use [Writing From a Shared Library](/computing-101/control-flow/callee-write).
If you debug the checker path directly, load the native harness with `gdb`, not `/challenge/check`, and redirect stand-in flag bytes into it:

```console
hacker@dojo:~$ python3 -c 'import sys; sys.stdout.buffer.write(b"debug-stale-stack-flag\n" * 16)' > fake-flag
hacker@dojo:~$ gdb --args /challenge/harness solve.so
(gdb) run < fake-flag
```

The harness reads stand-in flag bytes from stdin, just as the checker feeds it, and the checker output also prints the exact stale-stack offset for this level.
