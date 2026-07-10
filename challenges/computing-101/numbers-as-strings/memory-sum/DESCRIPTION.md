The boss: put it all together.

Read the numbers from `argv`, convert each one with your `atoi`, add them into a total, turn that total back into text with your `itoa`, and `write` it to standard output.
With no number arguments, print `0`.

- `argc` is at `[rsp]`; the 8-byte `argv` pointer entries begin at `[rsp + 8]`, and `[rsp + 16]` is the entry for `argv[1]`.
- Keep a cursor on each table entry from `argv[1]` through `argv[argc - 1]`.
- The cursor is the address of an entry; dereference that entry to obtain the string pointer that `atoi` expects.
- Advance the cursor by 8 bytes after each number.

`atoi` is a function call, so any loop state you still need afterward must be preserved according to the [calling convention rules you practiced earlier](/computing-101/control-flow/caller-saved-registers).

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
