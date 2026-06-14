You now know how to output data to stdout using `write`.
But how does your program receive input data?
It `read`s it from stdin!

Like `write`, `read` is a system call that shunts data around between file descriptors and memory, and its syscall number is `0`.
In `read`'s case, it reads some amount of bytes from the provided file descriptor and stores them in memory.
The C-style syntax is the same as `write`:

```c
read(0, some_address, 5);
```

This will read `5` bytes from file descriptor `0` (stdin) into memory starting from `some_address`.
So, if you type in (or pipe in) `HELLO HACKERS` into stdin, the above `read` call would result in the following memory configuration:

```text
     Address     │ Contents
+───────────────────────────+
│ some_address   │ 48       │
│ some_address+1 │ 45       │
│ some_address+2 │ 4c       │
│ some_address+3 │ 4c       │
│ some_address+4 │ 4f       │
+───────────────────────────+
```

What are those numbers??
They are _hexadecimal_ representations of _ASCII_-encoded letters.
If those words don't make sense, please run through the first half or so of the [Dealing with Data](/fundamentals/data-dealings) module and then come back here!

In this level, we will combine `read` with our previous `write` abilities.
The challenge will pipe the flag into your program's stdin.
Your program should:

1. first `read` the provided bytes from stdin to your program's memory
2. `write` those same bytes from that memory location to stdout
3. finally, exit with the exit code `42`.

But what address should you use?
You need somewhere that's valid and writable, and you already know about one such place: the stack!
The `rsp` register starts out pointing at the stack data that the kernel placed there when launching your program, such as argument information you've used in earlier levels.
In this level, you do not need that startup data after your program begins, so you can reuse the current stack memory as scratch space for `read`.
Later programs that still need values from `[rsp]` or nearby stack slots should avoid overwriting those bytes until they are done with them.
So you can just use `rsp` as your memory address: `mov rsi, rsp`.


----
**DEBUGGING:**
Having trouble?
Recall the Introspection module!
Build your program and run it with `strace` to see what's happening at the system call level, or run it in `gdb` to inspect the values of registers and memory to see what's unexpected.

**REMEMBER:**
You've basically already written steps 2 and 3 (though in the previous challenges, you loaded `rsi` from `[rsp+16]` --- here, you'll set it to `rsp` directly with `mov rsi, rsp`!).
All you have to do is add step 1!
