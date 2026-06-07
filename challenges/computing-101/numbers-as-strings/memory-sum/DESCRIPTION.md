The boss: put it all together.

Read the numbers from `argv`, convert each one with your `atoi`, add them into a total, turn that total back into text with your `itoa`, and `write` it to standard output.

- Walk `argv[1]` through `argv[argc - 1]`.
- `argc` is at `[rsp]`
- the `argv` pointers start at `[rsp + 8]` and 8 bytes long, so if you have one loaded into `rdi` (e.g., `mov rdi, rsp; add rdi, 8`), you can go to the next one by doing `add rdi, 8`).
- run `atoi` on each, summing as you go

The numbers, or even the overall sum, might be negative, which is exactly why your `atoi` and `itoa` handle the sign.
Then `itoa` the total into a scratch buffer (e.g., on the stack) and `write` that many bytes to file descriptor `1`.

Build and submit as before:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ /challenge/check prog
```

Sum them, convert the total, print it, and you're done!

----
**Debugging:**
Don't forget about gdb!
Insert `int3`, use `breakpoint` in gdb, `stepi` the instructions, and try to deeply understand failures if they occur so that you can fix it!
