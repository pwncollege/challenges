The stack stores more than just `argc` and `argv`!
Right after the argument list, the kernel places the **environment variables** you learned about in the [Linux Luminarium](/linux-luminarium).
Just like `argv`, these are stored on the stack as an array of pointers to strings, where each string includes both the name and value of the variable, as so: `PATH=/usr/bin:...`, `HOME=/home/hacker`, or `PWN=COLLEGE`.

If a program is called with no arguments (e.g., `argc` is 1 and the only string in `argv` is the name of the program itself) and a single environment variable named `FLAG`, its starting stack layout might look like this:

```text
     Address    │ Contents
   +────────────────────────+
   │ rsp + 0    │ 1         │ ◀─── argc
   +────────────────────────+
   │ rsp + 8    │ rsp + 128 │──┐  argv[0]: pointer to the program name
   +────────────────────────+  │
   │ rsp + 16   │ 0         │  │  NULL (end of argv)
   +────────────────────────+  │
   │ rsp + 24   │ rsp + 200 │──┼──┐  envp[0]: pointer to the first env var
   +────────────────────────+  │  │
   │ rsp + 32   │ 0         │  │  │  NULL (end of envp)
   +────────────────────────+  │  │
                               │  │
     Address    │ Contents     │  │
   +────────────────────────+  │  │
   │ rsp + 128  │ "/tmp/..."│◀─┘  │  the program name
   +────────────────────────+     │
   │ ...        │ ...       │     │
   +────────────────────────+     │
   │ rsp + 200  │ "FLAG=..."│◀────┘  the first env var: the `FLAG` variable
   +────────────────────────+
```

Two new things to notice:

1. Both `argv` and `envp` are **NULL-pointer-terminated**: the kernel writes a `NULL` pointer at the end of each list of pointers.
   That's how programs (and you!) know where each list ends --- walk the pointers until you hit a `NULL`.
   In the diagram, you can see the `NULL` at `rsp+16` marking the end of `argv`, and another at `rsp+32` marking the end of `envp`.

2. The `envp` strings look like `NAME=VALUE` (e.g., `PATH=/usr/bin:/bin`).
   So `envp[0]` points to a string that starts with the first env var's name.

In this challenge, we will set the `FLAG` environment variable to the actual flag and run your program with no arguments and no other env vars.
That means `[rsp+24]` will hold a pointer to the `FLAG=...` string, and you can get the flag by `write()`ing it out!
