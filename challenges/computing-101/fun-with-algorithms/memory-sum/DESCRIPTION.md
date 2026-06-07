Last level, your program read its *one* argument.
A program can be given *many*: run `./prog 3 4 5` and it gets three.

`argc` (at `[rsp]`) is how many arguments there are --- counting the program's own name.
The argument pointers follow it: `argv[0]` at `[rsp + 8]`, `argv[1]` at `[rsp + 16]`, `argv[2]` at `[rsp + 24]`, each one `8` bytes further along.

So loop from `argv[1]` to `argv[argc - 1]`, convert each one with your `atoi`, and add them into a running total.
Then exit with that total as your exit code.
(It's still one byte, so the numbers you're given will add up to something in `0`-`255`.)

Assemble and link it as a normal program, then submit it:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ /challenge/check prog
```

Sum the arguments, exit with the total, and score!
