Your scanner turns a line of text into values your program can use.
Now use a pathname from that input to choose which program runs next.

The [execve system call](https://man7.org/linux/man-pages/man2/execve.2.html) replaces the calling process with a program loaded from a file.
The process keeps its identity, but its instructions, stack, and other program memory become those of the new program.
A successful `execve` does not return to the old code.

On 64-bit x86 Linux, `execve` is syscall 59.
Its three arguments are a pointer to the pathname, a pointer to an `argv` array, and a pointer to an `envp` array.
You've already read these arrays from the starting stack; now you supply them to the kernel.
For this level, `argv` contains the pathname's pointer followed by a NULL pointer.
An empty environment is sufficient.

Write a program with a `.global _start` entry point that prints `$ `, reads a pathname from standard input, and executes that program.
Reuse your printing and scanning routines.
Each input arrives in one `read`, contains one absolute pathname followed by a newline, and is at most 255 bytes including the newline.
Reserve space for a terminating NUL byte.
There are no command arguments yet.

```console
hacker@dojo:~$ as -o shell.o shell.s
hacker@dojo:~$ ld -o shell shell.o
hacker@dojo:~$ ./shell
$ /usr/bin/pwd
/home/hacker
hacker@dojo:~$ /challenge/check shell
```

Execute the program named by the input, and get the flag!
