In the previous level, you tuned `argv[0]` from the shell with `env -i FOO=xxxxxxxx`.
The same trick from inside gdb is trickier: by default, gdb launches the inferior with its own full environment (your shell's env plus a few of gdb's own additions), so `argv[0]` ends up at a different address than the bare shell launch.

Gdb's fix is `set exec-wrapper`, which prepends a command to the inferior's `execve`:

```text
(gdb) set exec-wrapper env -i FOO=xxxxxxxx
(gdb) run
```

The `env -i FOO=xxxxxxxx` part is identical to what you did in the shell, so gdb's `execve` becomes identical to the shell's --- and your alignment math from the previous level carries over unchanged.

This level uses the same `/challenge/program` as before, but you have to align `argv[0]` to `0x5390` from **both** contexts: from the shell, and from inside gdb.
The flag appears once you've solved it in both.

----

**NOTE:**
Order doesn't matter --- solve under gdb first or from the shell first, whichever you like.
