The stack stores more than just `argc` and `argv`!
Right after the argument list, the kernel places the **environment variables** you learned about in the [Linux Luminarium](/linux-luminarium).
Just like `argv`, these are stored on the stack as an array of pointers to strings, where each string includes both the name and value of the variable, as so: `PATH=/usr/bin:...`, `HOME=/home/hacker`, or `PWN=COLLEGE`.

The structure looks like this (assuming `argc` is 1, so just the program name and no arguments, plus a single environment variable `FLAG=...`):

```text
     Address    │ Contents
   +────────────────────────+
   │ rsp + 0    │ 1         │ ◀─── argc
   +────────────────────────+
   │ rsp + 8    │ rsp + 128 │───────┐  argv[0]: pointer to the program name
   +────────────────────────+       │
   │ rsp + 16   │ 0         │       │  NULL (end of argv)
   +────────────────────────+       │
   │ rsp + 24   │ rsp + 200 │─────┐ │  envp[0]: pointer to the first env var
   +────────────────────────+     │ │
   │ rsp + 32   │ 0         │     │ │  NULL (end of envp)
   +────────────────────────+     │ │
                                  │ │
  ┌───────────────────────────────│─┘
  │                               │
  │   Address   │ Contents        │
  │ +──────────────────────────+  │
  │ │ rsp + 128 │ "/tmp/..."   │◀─┘ the program name
  │ +──────────────────────────+
  │ │ ...       │ ...          │
  │ +──────────────────────────+
  └▸│ rsp + 200 │ "FLAG=..."   │ ◀─ the first env var: the `FLAG` variable
    +──────────────────────────+
```

Two new things to notice:

1. There is a **NULL pointer** between `argv` and `envp`.
   The kernel uses this NULL to mark the end of `argv` --- that's how programs (and you!) tell where `argv` ends and `envp` begins.

2. The `envp` strings look like `NAME=VALUE` (e.g., `PATH=/usr/bin:/bin`).
   So `envp[0]` points to a string that starts with the first env var's name.

In this challenge, we will set the `FLAG` environment variable **to your actual flag** (padded out with `=` characters so that the whole `envp[0]` string is always **exactly 64 bytes long**), and run your program with no other env vars.
That means `[rsp+24]` will hold a pointer to those 64 bytes --- with the flag content sitting right there in memory, waiting to be written out.

Your task: write those 64 bytes from `envp[0]` straight to stdout!

1. Load the `envp[0]` pointer from `[rsp+24]`.
2. Use the `write` syscall to write 64 bytes starting at that pointer to file descriptor 1 (stdout).
3. `exit` cleanly with code `0`.

Recall that the `write` syscall takes:

- `rax`: `1` (the syscall number)
- `rdi`: the file descriptor (`1` for stdout)
- `rsi`: the buffer pointer (your `envp[0]` pointer)
- `rdx`: the number of bytes to write (`64`)

Get it right, and your program will print the flag for you, no further questions asked!
