You've now used GDB to inspect registers, step through instructions, examine memory, and even cooperate with the debugger via `int3`.
But here's something subtle, and crucial for the rest of your hacking journey: **the program's stack depends on how the program is launched.**

In particular, the *environment variables* you saw in the Stack module sit on the stack right after `argv`.
And those env vars come from whoever launched the program: your shell, or, when you're debugging, GDB.

Watch what happens.
The program `/challenge/debug-me` reads the *first byte* of the first environment variable's string into `rdi`, and then exits with that byte:

```text
mov    rdi,QWORD PTR [rsp+0x18]    <-- envp[0] pointer
movzx  rdi,BYTE PTR [rdi]          <-- first byte of the env var string
mov    rax,0x3c
syscall                            <-- exit(byte)
```

If you run it directly in your shell:

```text
hacker@dojo:~$ /challenge/debug-me
hacker@dojo:~$ echo $?
83
```

The exit code is `83` (the ASCII byte for `S`) because your shell's first env var happens to be `SHELL=/bin/bash` --- so envp[0] starts with `S`.
But your shell's environment is *not* what GDB will pass to the inferior!
We've configured the GDB launcher (`/challenge/bin/gdb`) to start the program with a *different* environment: a single env var of the form `<LETTER>=hello`, where `<LETTER>` is randomly chosen each time the container starts.

So when you run the program in GDB, it will exit with a *different* byte --- the ASCII value of that letter.
**That value is the secret you need to submit!**

To find it, launch GDB and either:

- run the program (`run`) and read the inferior's exit code from GDB's output (note: GDB displays it in octal, with a leading `0`, so `0115` is `77` in decimal), or
- step through the first two instructions (`starti`, `stepi`, `stepi`) and read `$rdi` (`print $rdi`).

Either way, the value you see is the secret, and it will *differ from what you'd see in the shell*.
That's the whole point: **the stack's contents reflect the environment the program was launched in, not some abstract truth about the program**.

Once you have the value, submit it with `/challenge/submit-number`.

----

**NOTE:**
This is one of the most common sources of confusion when learning to debug.
A bug that reproduces in the shell may not reproduce in GDB (and vice versa) precisely because GDB's environment is different.
GDB also tends to disable address-space layout randomization by default, so addresses you see in GDB may not match what the program sees outside of it.
Keep this in mind whenever you're debugging --- and whenever a bug seems to "go away" the moment you attach a debugger!
