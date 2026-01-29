So you've written your first program?
But until now, we've handled the actual building of it into an executable that your CPU can actually run.
In this challenge, _you_ will build it!

To build an executable binary, you need to:

1. Write your assembly in a file (often with a `.S` or `.s` syntax. We'll use `program.s` in this example).
2. Assemble your assembly file into an _object file_ (using the `as` command).
3. Link one or more executable object files into a final executable binary (using the `ld` command)!

Let's take this step by step:

**Writing assembly.**  
The assembly file contains, well, your assembly code.
For the previous level, this might be:

```console
hacker@dojo:~$ cat program.s
mov rdi, 42
mov rax, 60
syscall
hacker@dojo:~$
```

But it needs to contain _just a tad more info_.
We mentioned that we're using the _Intel_ assembly syntax in this course, and we'll need to let the assembler know that.
You do this by prepending a directive to the beginning of your assembly code, as such:

```console
hacker@dojo:~$ cat program.s
.intel_syntax noprefix
mov rdi, 42
mov rax, 60
syscall
hacker@dojo:~$
```

`.intel_syntax noprefix` tells the assembler that you will be using Intel assembly syntax, and specifically the variant of it where you don't have to add extra prefixes to every instruction.
It isn't actually an x86 instruction (like `mov` and `syscall`), and so it doesn't end up in our final executable binary or runs on the CPU.
We'll talk about other directives later, but for now, we'll let the assembler figure it out!

**Assembling Assembly Code into Object Files.**  
Next, we'll assemble the code.
This is done using the **as**sembler, `as`, as so:

```console
hacker@dojo:~$ ls
program.s
hacker@dojo:~$ cat program.s
.intel_syntax noprefix
mov rdi, 42
mov rax, 60
syscall
hacker@dojo:~$ as -o program.o program.s
hacker@dojo:~$ ls
program.o   program.s
hacker@dojo:~$
```

Here, the `as` tool reads in `program.s`, assembles it into binary code, and outputs an _object file_ called `program.o`.
This object file has actual assembled binary code, but it is not yet ready to be run.
First, we need to _link_ it.

**Linking Object Files into an Executable.**  
In a typical development workflow, source code is compiled and assembly is assembled to object files, and there are typically many of these (generally, each source code file in a program compiles into its own object file).
These are then _linked_ together into a single executable.
Even if there is only one file, we still need to link it, to prepare the final executable.
This is done with the `ld` (stemming from the term "**l**ink e**d**itor") command, as so:

```console
hacker@dojo:~$ ls
program.o   program.s
hacker@dojo:~$ ld -o program program.o
ld: warning: cannot find entry symbol _start; defaulting to 0000000000401000
hacker@dojo:~$ ls
program.o   program.s   program
hacker@dojo:~$
```

This creates an `program` file that we can then run!
Here it is:

```console
hacker@dojo:~$ ./program
hacker@dojo:~$ echo $?
42
hacker@dojo:~$
```

In the shell, `$?` holds the exit code of the last executed command.

Neat!
Now you can build programs.
In this challenge, go ahead and run through these steps yourself.
Build your executable, and pass it to `/challenge/check` for the flag!

----
**_start?**  
The attentive learner might have noticed that `ld` prints a warning about `entry symbol _start`.
The `_start` symbol is, essentially, a note to `ld` about where in your program execution should begin when the ELF is executed.
The warning states that, absent a specified `_start`, execution will start right at the beginning of the code.
This is just fine for us!

If you want to silence the error, you can specify the `_start` symbol, in your code, as so:

```console
hacker@dojo:~$ cat program.s
.intel_syntax noprefix
.global _start
_start:
mov rdi, 42
mov rax, 60
syscall
hacker@dojo:~$ as -o program.o program.s
hacker@dojo:~$ ld -o program program.o
hacker@dojo:~$ ./program
hacker@dojo:~$ echo $?
42
hacker@dojo:~$
```

There are two extra lines here.
The second, `_start:`, adds a _label_ called start, pointing to the beginning of your code.
The first, `.global _start`, directs `as` to make the `_start` label _globally visible_ at the linker level, instead of just locally visible at the object file level.
As `ld` is the linker, this directive is necessary for the `_start` label to be seen.

For all the challenges in this dojo, starting execution at the beginning of the file is just fine, but if you don't want to see those warnings pop up, now you know how to prevent them!
