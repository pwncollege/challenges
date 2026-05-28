You've now seen the `solve` shape from a few angles: you've received arguments, returned values, and called through a function pointer.
This challenge is also a `solve` function inside a shared library --- but **the grader passes you no arguments**.
Nothing in `rdi`, nothing in `rsi`. Just `call solve`.

The secret you have to return isn't anywhere obvious.
It's sitting on the **stack**, inside the caller's own frame, and you have to reach over and grab it.

**How is that possible?**  
Because of what `call solve` actually did. Let's walk through it.

Right before the grader's `caller` function executed `call solve`, the stack looked like this:

```text
                                          [higher addresses]
   +───────────────────────────────────+
   │ ... main's frame ...              │
   +───────────────────────────────────+
   │ return address (back to main)     │
   +───────────────────────────────────+
   │ caller's saved rbp                │
   +───────────────────────────────────+
   │ caller's local region (0x40 bytes)│
   │ ... the secret is in here ...     │
   +───────────────────────────────────+  ◀── rsp, immediately before `call solve`
                                          [lower addresses]
```

The `call solve` instruction does two things:

1. Pushes the return address onto the stack (8 bytes). **Pushing decrements `rsp`**, so the return address ends up at a _lower_ address than what was already on the stack.
2. Jumps to your code.

That first step is what "the stack grows downward" actually means.
Every `push`, every `call`, every `sub rsp, N` --- they all move `rsp` _down_ in memory.
Whatever was on the stack before you arrived sits at _higher_ addresses than your current `rsp`.

So at the moment your `solve` starts running, the stack looks like this:

```text
                                          [higher addresses]
   +───────────────────────────────────+
   │ ... main's frame ...              │
   +───────────────────────────────────+
   │ return address (back to main)     │
   +───────────────────────────────────+
   │ caller's saved rbp                │
   +───────────────────────────────────+
   │ caller's local region (0x40 bytes)│
   │ ... the secret is in here ...     │
   +───────────────────────────────────+
   │ return address (back to caller)   │  ◀── rsp points here
   +───────────────────────────────────+
                                          [lower addresses, where rsp goes if you grow your own frame]
```

The caller's locals are _above_ your `rsp`. The secret is _above_ your `rsp`.
To find it, you index into memory with a **positive** offset from `rsp`.

If you go the other way --- negative offsets, _below_ `rsp` --- you'll find unallocated stack space at best, and a guard-page segfault at worst.
There's nothing useful for you down there.
The lesson here is structural: **your caller is above you**, because the act of calling you pushed the stack downward.

**The task.**  
The grader's `caller` is laid out very specifically (it's hand-written assembly, so the offsets are guaranteed).
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
The grader will generate a different random secret for each run, so hardcoding won't work --- but the offset is always the same.

As before, build a shared library and pass it to the grader:

```console
hacker@dojo:~$ as -o your-solve.o your-solve.s
hacker@dojo:~$ ld -shared -o your-solve.so your-solve.o
hacker@dojo:~$ /challenge/check your-solve.so
```
