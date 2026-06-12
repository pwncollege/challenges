In addition to storing scratch data and return addresses, the stack stores the _local variables_ of functions: data they use for functionality that's not necessarily needed by other functions of a program.
In security situations where a hacker gets ``code execution'' inside a process, these variables are an open book: there is nothing preventing code in a process from reading data from all over the stack!

This challenge explores this concept.
Once again, you write a `solve` function that the challenge calls, but **the challenge passes you no arguments**.
Instead, the challenge's `caller` function has stored the flag in its own local variables before calling you.
You have to reach over into the caller's "frame" (what we call the part of the stack including a function's local variables and the saved return address to which it will return) and grab those bytes.

**Wait, what?**  
Let's walk through why this is possible.
In this challenge, the `main` function calls the `caller` function, which then calls your `solve` function.
Right before the challenge's `caller` function executed `call solve`, the stack looked like this:

```text
                                          [smaller addresses]
   +───────────────────────────────────+  ◀── rsp, immediately before `call solve`
   │ caller's local region             │
   │ ... your flag is in here ...      │
   +───────────────────────────────────+
   │ caller's saved rbp                │
   +───────────────────────────────────+
   │ return address (back to main)     │
   +───────────────────────────────────+
   │ ... main's frame ...              │
   +───────────────────────────────────+
                                          [larger addresses]
```

The `call solve` instruction does two things:

1. Pushes the return address onto the stack (8 bytes). **Pushing decrements `rsp`**, so the return address ends up at a _smaller_ address than what was already on the stack.
2. Jumps to your code.

That first step is critical: the stack grows backwards from what you might expect.
`pop` actually adds 8 to `rsp`, and `push` subtracts 8.
This is counter-intuitive and is a concept that often confuses learners.
If you think of the stack as a page that is 8 bytes wide, you would start writing in this page at the very bottom, and move one line upwards on the page every time you `push`.
In other words, say, `pop rdi` is equivalent to `mov rdi, [rsp]; add rsp, 8` and `push rdi` is equivalent to `sub rsp, 8; mov [rsp], rdi`.

Note that this makes talking about the stack without confusion borderline impossible.
For example, people with a math background tend to think of a coordinate of 0 as being on the bottom or the left of a page, whereas people with a video game or web development background tend to think of 0 as being on the top or the left.
This leads to massive confusion about the definition of "higher address", "lower address", and so on.
Everyone has different ways of dealing with this.
In this document, because horizontal space is at a premium, we put diagrams from 0 (top) to 0xffffffff (bottom), but in everyday life when not restricted by horizontal space, we simply conceptualize memory from the "left" (0) to the "right" (0xffffffff).

Anyways, at the moment your `solve` starts running, the stack looks like this:

```text
                                          [smaller addresses, where rsp goes if you grow your own frame]
   +───────────────────────────────────+
   │ return address (back to caller)   │  ◀── rsp points here
   +───────────────────────────────────+
   │ caller's stack frame              │
   │ ... your flag is in here ...      │
   +───────────────────────────────────+
   │ return address (back to main)     │
   +───────────────────────────────────+
   │ ... main's frame ...              │
   +───────────────────────────────────+
                                          [larger addresses]
```

The caller's locals sit at _larger_ addresses than your `rsp` --- below your `rsp` in the diagram. The data you want is somewhere in that region.
To find it, you index into memory with a **positive** offset from `rsp`.

If you go the other way --- negative offsets, at addresses _smaller_ than `rsp` (above `rsp` in the diagram) --- you'll find unallocated stack space.
There's nothing useful for you up there (yet!).

When your `solve` starts running, the layout looks like this:

```text
   [rsp + 0x00]   your return address (back into caller's code)
   [rsp + 0x08]   first byte of caller's local region
   ...
   [rsp + 0x40]   the flag (copied here by the caller)
   ...
   [rsp + 0x110]  caller's return address (back to main)
```

Your job: reach into the caller's frame, grab the flag at `[rsp + 0x40]`, and `write` it to stdout (you already know how to issue a `write` syscall!).
Get it right, and your `solve` will print the flag for you!
