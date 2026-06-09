In the last level you reached into the *caller's* frame to read data it left for you.
Now you'll build a frame of your own.

So far, your functions have kept everything in registers.
But there are only sixteen of them, and some jobs need more room than that.
Here's one: count how many *distinct* byte values appear in a buffer.
The natural way is to keep a tally with one slot per possible byte value --- 256 slots --- marking a slot the first time you see its byte, then counting the marked slots at the end.
256 slots will never fit in registers.
You need actual memory, and a function gets its own scratch memory by carving it out of the stack.

Recall that the stack grows *downward*: subtracting from `rsp` moves it to a lower address and leaves the region between the old and new `rsp` free for you to use.
So `sub rsp, 256` reserves 256 bytes of scratch space; your slots live at `[rsp]` through `[rsp+255]`, indexed by byte value.
This reserved region is your function's *stack frame*.

Functions conventionally anchor their frame with `rbp`, so the frame's contents stay at fixed offsets even as `rsp` moves around underneath:

```
push rbp           # save the caller's rbp
mov  rbp, rsp      # rbp now marks the top of our frame
sub  rsp, 256      # reserve 256 bytes of locals below it
    ...            # use [rsp] .. [rsp+255] as your scratch space
mov  rsp, rbp      # discard the locals
pop  rbp           # restore the caller's rbp
ret
```

That last part matters as much as the first: before you `ret`, you must put the stack back exactly as you found it.
The `ret` pops its return address off the stack, so if `rsp` isn't where it started, `ret` jumps somewhere random and your program crashes.
(One more detail: the stack starts as whatever bytes were left there before --- it is not zeroed. Clear your slots before you tally into them.)

Write a function called `solve` that takes a pointer to a buffer in `rdi` and a length in `rsi`, and returns, in `rax`, the number of distinct byte values among those `rsi` bytes.

Build it into a shared library and hand it to the grader:

```console
hacker@dojo:~$ as -o solve.o solve.s
hacker@dojo:~$ ld -shared -o solve.so solve.o
hacker@dojo:~$ /challenge/check solve.so
```
