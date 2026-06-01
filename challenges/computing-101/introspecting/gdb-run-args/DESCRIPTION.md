In the previous level, you used gdb's `run` command for the first time: `run` starts the program and lets it execute freely.
But what if the program _needs command-line arguments_ to work?

Outside gdb, you've been passing arguments by just typing them after the program name:

```console
hacker@dojo:~$ /challenge/debug-me hello
```

Inside gdb, the analog is to pass them to `run`:

```text
(gdb) run hello
```

Whatever you put after `run` becomes the inferior's `argv[1]`, `argv[2]`, and so on --- exactly as if you'd typed those arguments on the shell command line.
GDB also accepts the short form `r`:

```text
(gdb) r hello
```

(Anywhere you see `run` in gdb's docs, `r` works too.)

In this challenge, `/challenge/debug-me` only prints your flag when you give it the string `pwn` as `argv[1]`.
Do it!
