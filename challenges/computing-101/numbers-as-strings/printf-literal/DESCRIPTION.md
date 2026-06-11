You can already write bytes to standard output.
Now you will put that in a loop and start building a small `printf`-style program.

The input is a **format string** in `argv[1]`.
For this first level, there are no special markers yet.
Every byte in the format string is ordinary text, so your job is to write those bytes to standard output.

```
argv[1]:  "score: "
output:   "score: "
```

You can write one byte at a time as you scan, or find a run of ordinary bytes and write the whole run at once.
Either way, stop when you reach the format string's NUL byte, then exit cleanly.

Build and submit it as an executable:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ ./prog 'score: '
score: hacker@dojo:~$ /challenge/check prog
```

Note that in the above, `prog` doesn't print a terminal null byte, and the command prompt starts on the same line.
That's okay --- we'll learn to write out newlines later!

When testing, be aware that the commandline also has a built-in `printf` utility.
If you name your program `printf`, make sure to run it via a path (e.g., `./printf`) to avoid the built-in one.

----
**NOTE:**
