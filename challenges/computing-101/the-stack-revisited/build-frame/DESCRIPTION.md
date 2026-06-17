In the last level, you reserved a stack frame, cleared it, restored `rsp`, and returned safely.
Now you'll put that frame to work.

Count how many *distinct* byte values appear in a buffer.
The natural way is to keep a table with one slot per possible byte value: 256 slots, indexed by the byte value itself.
Start with the same 256-byte stack frame you built before and clear it to zero.
Then, when you see byte value `b`, write `1` into slot `b`.
After you have scanned the buffer, count how many table slots are marked.

Write a function called `solve` that takes a pointer to a buffer in `rdi` and a length in `rsi`, and returns, in `rax`, the number of distinct byte values among those `rsi` bytes.
You might find the instruction `mov byte ptr [rsp+rcx], 1` useful for marking a given value (stored in `rcx`) as "present" in your scratch table (based at `rsp`).

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```

----
**HINT:**
You'll need three loops in this level, one after the other: one to clear the scratch table, one to mark each value you see, and one to count the marked slots afterwards.

For debugging a submitted function inside a shared library, refer back to [Writing From a Shared Library](/computing-101/control-flow/callee-write).
