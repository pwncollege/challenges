In the previous level, you read `argv[1]` from the stack.
But the stack stores more than just `argc` and `argv`!

Right after the argument list, the kernel places **environment variables**: the strings like `PATH=/usr/bin:...` or `HOME=/home/hacker` that you might have seen in your shell.
Just like `argv`, these are stored on the stack as an array of pointers to strings.

The structure looks like this (assuming `argc` is 1, so just the program name and no arguments):

```text
    Address    │ Contents
  +────────────────────────+
  │ rsp + 0    │ 1         │  ◀── argc
  +────────────────────────+
  │ rsp + 8    │ argv[0]   │──── pointer to the program name
  +────────────────────────+
  │ rsp + 16   │ 0         │  ◀── NULL (end of argv)
  +────────────────────────+
  │ rsp + 24   │ envp[0]   │──── pointer to the first env var string
  +────────────────────────+
  │ rsp + 32   │ envp[1]   │──── pointer to the second env var string
  +────────────────────────+
  │ ...        │ ...       │
  +────────────────────────+
  │ rsp + N    │ 0         │  ◀── NULL (end of envp)
  +────────────────────────+
```

Two new things to notice:

1. There is a **NULL pointer** between `argv` and `envp`.
   The kernel uses this NULL to mark the end of `argv` --- that's how programs (and you!) tell where `argv` ends and `envp` begins.

2. The `envp` strings look like `NAME=VALUE` (e.g., `PATH=/usr/bin:/bin`).
   The first byte of `envp[0]`'s string is just the first character of the *name* of the first environment variable.

In this challenge, we will run your program with **only one environment variable** (something like `A=hello`, `B=hello`, etc., chosen at random), and `argc` will be `1`.
That means `[rsp+24]` will hold a pointer to a string like `"A=hello"`, and the first byte of that string will be the letter `A`.

Read the first byte of the `envp[0]` string and exit with it!

Just like `argv[1]`, this requires **two dereferences**: one to get the `envp[0]` pointer from the stack, and one to follow that pointer to read the first byte of the string.
