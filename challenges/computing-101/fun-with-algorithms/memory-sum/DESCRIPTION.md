The capstone: put it all together.

Read the numbers from `argv`, convert each one with your `atoi`, add them into a total, turn that total back into text with your `itoa`, and `write` it to standard output.
That's the whole pipeline:

```
print(itoa(sum(atoi(a) for a in argv)))
```

Walk `argv[1]` through `argv[argc - 1]` (`argc` is at `[rsp]`, the pointers start at `[rsp + 8]`), running `atoi` on each and summing as you go.
The sum can be negative, which is exactly why your `itoa` handles the sign.
Then `itoa` the total into a scratch buffer (a few bytes of `.bss`, or room on the stack) and `write` that many bytes to file descriptor `1`.

No exit-code limit this time --- you're *printing* the answer, so it can be any size, positive or negative.

Build and submit as before:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ /challenge/check prog
```

Sum them, convert the total, print it, and score!
