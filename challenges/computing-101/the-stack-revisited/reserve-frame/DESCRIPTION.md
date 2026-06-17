In the last level you reached *up* the stack into the caller's frame.
Now you'll carve out a frame of your own.

So far, your functions have kept their temporary values in registers.
But a function can need more scratch space than registers can hold.
On 64-bit x86, a function makes stack scratch space by moving `rsp` to a lower address: `sub rsp, 256` reserves 256 bytes below the current stack pointer.
Those bytes are then addressable as `[rsp]` through `[rsp+255]`.

This does not give you freshly-zeroed bytes.
The region below `rsp` is ordinary stack memory, and it may contain bytes left behind by earlier code.
If you use those bytes as a table or a set of counters, stale values look exactly like values your function wrote.
That is why a stack frame that will hold scratch data normally starts with initialization: reserve the space, write known values into it, use it, then put `rsp` back before returning.

In full, the shape is:

```asm
sub rsp, 256       # reserve 256 bytes of scratch below the stack pointer
    ...            # initialize and use [rsp] through [rsp+255]
add rsp, 256       # give the space back
ret
```

That last step matters as much as the first.
`ret` pops its return address from `[rsp]`, so if `rsp` is not back where it started, `ret` will read the wrong bytes as an address and your program will crash.

Write a function called `solve` that reserves a 256-byte stack frame, clears every byte in it to zero, restores `rsp`, and returns.
The grader fills the would-be frame with nonzero bytes before calling your function, then checks that all 256 bytes were cleared after your function returns.
You may find `mov byte ptr [rsp+rcx], 0` useful for clearing one byte at offset `rcx`.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```

For debugging a submitted function inside a shared library, refer back to [Writing From a Shared Library](/computing-101/control-flow/callee-write).
