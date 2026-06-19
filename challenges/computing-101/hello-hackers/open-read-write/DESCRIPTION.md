So far, your program has only interacted with stdin and stdout, but what about files on disk?
To access a file, you first need to `open` it using the `open` system call.

The `open` system call (syscall number `2`) takes a pointer to a filename string and returns a brand-new file descriptor referring to that file:

```c
open("/flag", 0);
```

The second argument specifies additional modes and permissions for the file, but `0` requests the default: read-only.

The registers for `open` follow the same convention:

| Register | Purpose |
|----------|---------|
| `rax`    | `2` (syscall number for `open`) |
| `rdi`    | pointer to the filename string in memory |
| `rsi`    | `0` (read-only) |

When `open` returns, `rax` contains the new file descriptor (fd) number.
Recall that file descriptor 0 is stdin, file descriptor 1 is stdout, and file descriptor 2 is stderr.
Other files that are open are just represented by other file descriptors, incrementing from 3 onwards!
You'll use this fd as the first argument to `read`, just like you did for stdin earlier, but this time `read` will read from your file.

How to load the filename into memory?
In this level, the path to the flag (`/flag`) will be passed as the first argument to your program.
You already know how to load that: `mov rdi, [rsp+16]`.

Your program should:

1. Load a pointer to the filename (stored at `[rsp+16]`, the first argument) into `rdi`
2. Specify the default of read access for the second argument (set `rsi` to `0`).
3. `open` it (syscall `2`)
4. `read` 64 bytes from the returned fd into memory. The returned fd will be stored in `rax`; you'll need to move that to `rdi` for `read`'s first argument. Make sure to do this _before_ you set the syscall number for write!
5. `write` those 64 bytes to stdout
6. `exit` with code `42` (syscall `60`)

----
**DEBUGGING:**
Having trouble?
Use `strace` to see your system calls in action --- it will show you exactly what arguments each syscall receives and what it returns.
If `open` is returning `-1`, double-check your filename pointer.
If `read` returns `0`, the file descriptor from `open` might be wrong.
