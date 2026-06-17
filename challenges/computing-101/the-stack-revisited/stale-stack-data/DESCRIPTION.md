In the last level, you read data sitting to the right of your current `rsp`, inside your caller's frame.
Now you'll look the other way.

When your code calls a function, that callee can move `rsp` left and use stack memory of its own.
When it returns, it moves `rsp` back right, but the bytes it wrote are not automatically erased.
They become stale stack data: ordinary memory left behind by code that already finished.

This challenge passes your `solve` a pointer to a function named `read_flag`.
Call that function first.
It puts the flag in its own stack frame and returns.
After it returns, that old frame is to the left of your current `rsp`, and the flag bytes are still there until something overwrites them.

Write a function called `solve` that calls the function pointer in `rdi`, then writes the stale flag bytes from the old callee frame to stdout.
Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```

For debugging a submitted function inside a shared library, refer back to [Writing From a Shared Library](/computing-101/control-flow/callee-write).
