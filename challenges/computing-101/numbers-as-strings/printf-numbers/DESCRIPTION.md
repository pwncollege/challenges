One `%d` marker lets the format string include one changing number.
Real messages often need more than one value.

Now support several `%d` markers in the same format string.
Each `%d` consumes the next command-line value, so your program needs to remember which `argv` entry comes next.

```
argv[1]:  "opened %d files and skipped %d"
argv[2]:  "7"
argv[3]:  "3"
output:   "opened 7 files and skipped 3"
```

The first `%d` uses `argv[2]`, the second uses `argv[3]`, and so on.
After printing one number, continue scanning the format string after that marker.

Build and submit as before:

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ ./prog 'opened %d files and skipped %d' 7 3
opened 7 files and skipped 3
hacker@dojo:~$ /challenge/check prog
```

Consume the decimal arguments in order, and score!
