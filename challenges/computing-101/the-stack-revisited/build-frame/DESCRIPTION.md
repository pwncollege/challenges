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
Note that this doesn't bring any new memory into existence!
The stack memory was already there, it's just that `rsp` was pointing to one specific place inside it before the `sub`, and after the `sub` it will be pointing a bit further "left", so stack accesses using `rsp` (e.g., `mov [rsp], XYZ`, `mov XYZ, [rsp]`, `pop`) will have more previously-_unused_ memory to play with.
This reserved region is your function's *stack frame*.

In full, the pattern is reserve, use, then put it back:

```
sub rsp, 256       # reserve 256 bytes of scratch below the stack pointer
    ...            # use [rsp] .. [rsp+255] as your slots
add rsp, 256       # give the space back
ret
```

That last step matters as much as the first: `ret` pops its return address off the stack, so if `rsp` isn't back where it started, `ret` jumps somewhere random and your program crashes.
As long as you don't `push` or `pop` anything inside the function, `rsp` stays put, and your slots sit at the same `[rsp + ...]` offsets the whole time.
(One more detail: the stack starts as whatever bytes were left there before --- it is not zeroed. Clear your slots before you tally into them.)

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
You'll need _two_ loops in this level, one after the other: one to mark each value you see, and another one to count them afterwards.

**Debugging your solution.**
Because your submitted code is a function inside a shared library, there is no `_start` for `gdb` to run directly.
For a debugging build, add a temporary `_start` that sets up a small byte buffer, calls `solve`, and then exits with the return value.
Keep your `.global solve` and `solve:` function in the same file; this `_start` is just extra scaffolding for the debug executable.

```asm
.global _start
_start:
    lea rdi, [rip+sample]        # first argument: pointer to bytes
    mov rsi, sample_end-sample   # second argument: number of bytes
    int3                         # optional: gdb breaks here
    call solve
    mov rdi, rax                 # exit code = returned distinct count
    mov rax, 60
    syscall

sample:
    .byte 0x41, 0x42, 0x41, 0x43
sample_end:
```

Assemble and link that version as a normal executable, then run it in `gdb`:

```console
hacker@dojo:~$ as -o debug.o debug.s
hacker@dojo:~$ ld -o debug debug.o
hacker@dojo:~$ gdb ./debug
(gdb) run
```

Step through from the `int3`, watch `rsp` before and after `solve`, and make sure your function reaches `ret` with `rsp` restored.
When you are ready to submit, build the shared library version with `ld -shared` as usual.
