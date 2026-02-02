Why is the stack called a *stack*?
So far, we've just used it as a region of memory that we read from with `mov`, like any other memory dereference.
But the stack is meant to be used as, well, a stack of data: you `pop` values off the top!

The `pop` instruction is purpose-built for this.
`pop rdi` does two things:

1. Reads the value at `[rsp]` into `rdi` (just like `mov rdi, [rsp]`).
2. Adds 8 to `rsp`, advancing the stack pointer to the next value.

Using the same example as before:

```text
hacker@dojo:~$ /tmp/your-program hello world
```

Before the `pop rdi`:

```text
    Address    │ Contents
  +───────────────────────+
  │ ...        │ ...      │
  +───────────────────────+
┌▸│ 1337000    │ 3        │  ◀── the argument count
│ +───────────────────────+
│ | 1337008    | ???      |
│ +───────────────────────+
│
└────────────────────────────┐
                             │
   Register │ Contents       │
  +────────────────────────+ │
  │ rsp     │ 1337000      │─┘
  +────────────────────────+
  │ rdi     │ 0            │
  +────────────────────────+
```

After the `pop rdi`:

```text
    Address    │ Contents
  +───────────────────────+
  │ ...        │ ...      │
  +───────────────────────+
  │ 1337000    │ 3        │
  +───────────────────────+
┌▸| 1337008    | ???      |
│ +───────────────────────+
│
└────────────────────────────┐
                             │
   Register │ Contents       │
  +────────────────────────+ │
  │ rsp     │ 1337008      │─┘
  +────────────────────────+
  │ rdi     │ 3            │
  +────────────────────────+
```

The value `3` was popped off the top of the stack into `rdi`, and `rsp` advanced by 8 bytes to point to the next value.
The data at `1337000` is still there in memory, but as far as the stack is concerned, it's been removed: `rsp` has moved past it.

In this challenge, use `pop` to read the argument count and exit with it!
