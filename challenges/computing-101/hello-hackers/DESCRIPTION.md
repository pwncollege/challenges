Until now, your program's single interaction with the wider world was changing its exit code when `exit`ing.
Of course, more interaction is possible!

In this module, we will learn about the `write` system call, which is used to `write` output to the command-line terminal!
This is going to be an exciting journey: the logic of this program is going to be both as close as you can possibly get to the hardware itself (e.g., you are writing raw x86 assembly that the CPU directly understands!) and as close as you can possibly get to the Linux operating system (e.g., you are triggering system calls directly!).
