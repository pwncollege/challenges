In the previous levels, arguments were already configured for you.
Now it's your turn to set them yourself.

GDB lets you configure command-line arguments with `set args`. This lets you _simulate_ running the program with different arguments without actually relaunching GDB.

```gdb
(gdb) set args arg1 arg2 arg3
```

After this, when you start the program (e.g., via `starti`), it will run as if you launched:

```console
hacker@dojo:~$ /challenge/debug-me arg1 arg2 arg3
```

In this level, using `set args` **is mandatory**.
The program requires **exactly two arguments**. If you provide any other number of arguments, the program exits before it reveals the secret.

Also, passing arguments directly outside gdb will not help you solve this level!
For example, running:

```console
hacker@dojo:~$ /challenge/debug-me hello world
Trace/breakpoint trap
```

Will not work, and this is intentional. The program stops at `int3` (a breakpoint) before it can reveal the secret, and this is to force you to use gdb and set the arguments there.

When the arguments are set correctly, the secret will be loaded into the `rdi` register. At that point, you can recover it with:

```gdb
(gdb) print $rdi
```

Go and do that!

1. Launch gdb on `/challenge/debug-me`
2. Run `set args <arg1> <arg2>` (exactly 2 arguments), arg1 and arg2 can be anything
3. Start the program (`starti`), then continue (`continue`)
4. Read the secret with `print $rdi`
5. Submit with `/challenge/submit-number`

----

**NOTE:**
This level expects you to use `set args` from inside gdb.
Other forms exist (such as launching with `gdb --args ...`, or from inside gdb using `run arg1 arg2`), but they are out of scope for this level.
