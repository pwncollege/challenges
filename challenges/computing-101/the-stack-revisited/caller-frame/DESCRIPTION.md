Let's dig a bit into the stack.
In addition to storing scratch data and return addresses, the stack stores the _local variables_ of functions: data they use for functionality that's not necessarily needed by other functions of a program.
In security situations where a hacker gets ``code execution'' inside a process, these variables are an open book: there is nothing preventing code in a process from reading data from all over the stack!

This challenge explores this concept.
Once again, you write a `solve` function that the challenge calls, but **the challenge passes you no arguments**.
The secret you have to return isn't anywhere obvious.
It's sitting on the **stack**, inside the caller's own "frame" (what we call the part of the stack including a function's local variables and the saved return address to which it will return), and you have to reach over and grab it.

**Wait, what?**  
Let's walk through why this is possible.
In this challenge, the `main` function calls the `caller` functionm, which then calls your `solve` function.
Right before the challenge's `caller` function executed `call solve`, the stack looked like this:

```text
                                          [smaller addresses]
   +───────────────────────────────────+  ◀── rsp, immediately before `call solve`
   │ caller's local region (0x40 bytes)│
   │ ... the secret is in here ...     │
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
In other words, say, `pop rdi` is equivalent to `mov rdi, [rsp]; add rsp, 8` and `push rdi` is equivalent to `mov [rsp], rdi; sub rsp, 8`.

Note that this makes talking about the stack without confusion borderline impossible.
For example, people with a math background tend to thing of a coordinate of 0 as being on the bottom or the left of a page, whereas people with a video game or web development background tend to think of 0 as being on the top or the left.
This leads to massive confusion about the definition of "higher address", "lower address", and so on.
Everyone has different ways of dealing with this.
In this document, because horizontal space is at a premium, we put diagrams from 0 (top) to 0xffffffff (bottom), but in everyday life when not restricted by horizontal space, we simply conceptualize memory from the "left" (0) to the "right" (0xffffffff).

Anyways, at the moment your `solve` starts running, the stack looks like this:

```text
                                          [smaller addresses, where rsp goes if you grow your own frame]
   +───────────────────────────────────+
   │ return address (back to caller)   │  ◀── rsp points here
   +───────────────────────────────────+
   │ caller's local region (0x40 bytes)│
   │ ... the secret is in here ...     │
   +───────────────────────────────────+
   │ caller's saved rbp                │
   +───────────────────────────────────+
   │ return address (back to main)     │
   +───────────────────────────────────+
   │ ... main's frame ...              │
   +───────────────────────────────────+
                                          [larger addresses]
```

The caller's locals sit at _larger_ addresses than your `rsp` --- below your `rsp` in the diagram. The secret is somewhere in that region.
To find it, you index into memory with a **positive** offset from `rsp`.

If you go the other way --- negative offsets, at addresses _smaller_ than `rsp` (above `rsp` in the diagram) --- you'll find unallocated stack space at best, and a program crash at worst.
There's nothing useful for you up there (yet!).
The lesson here is structural: **your caller lives at larger addresses than you**, because the act of calling you pushed `rsp` to a smaller address.

**The task.**  
The challenge's `caller` is laid out very specifically.
When your `solve` starts running, the layout is:

```text
   [rsp + 0x00]   return address (back into caller's code)
   [rsp + 0x08]   first byte of caller's 0x40-byte local region
   ...
   [rsp + 0x40]   the secret (an 8-byte value)
   [rsp + 0x48]   caller's saved rbp
   [rsp + 0x50]   return address (back to main)
```

Read the secret at `[rsp + 0x40]`, put it in `rax` (the return-value register), and `ret`.
The challenge will generate a different random secret each run, so hardcoding won't work --- but the offset is always the same.
Get the secret back to the challenge, and it'll give you the flag!
