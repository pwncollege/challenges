By default, gdb launches programs with some changes to the environment, starting with your shell's env and adding a few environment variables of its own.
As a result, as you learned in the previous level, the stack gets shifted, and subtle code like tricky exploits might behave differently, leading to frustration during debugging.

This challenge will teach you how to achieve identical stack layouts in and outside of gdb.
We are going to use gdb's `set exec-wrapper` functionality, which prepends a command that will be used to actually run the program being debugged.
In this case, we'll set this command to `env -i`, which will wipe the environment (including whatever gdb adds) and let us control it directly.

```text
(gdb) set exec-wrapper env -i NAME=VALUE
(gdb) run
```

This is a new use of `env` than what you've seen before.
In the Linux Luminarium's [Variables module](/linux-luminarium/variables), you've used `env` to print out variables, but it can also be used as a variable-modifying launcher program: `env -i NAME=VALUE my_program` will launch `my_program` with an empty environment (`-i` means "re**i**nitialize environment") except for the `NAME` environment variable set to the value `VALUE`.
Since gdb appends your program name to the `exec-wrapper` command and invokes it, that's exactly what will happen!

This challenge will force you to confront this concept.
It uses the same kind of `/challenge/program` as before: it picks a target close to the current `argv[0]` on the first run and tells you what to hit.
You have to hit that target from **both** contexts --- once from the shell, and once from inside gdb (and the two contexts get separate targets, since gdb's environment isn't quite the same as the shell's).
The flag appears after you've solved it in both!

----
**NOTE:**
Order doesn't matter, solve under gdb first or from the shell first, whichever you like.
