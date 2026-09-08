Your launcher runs a command, but a successful `execve` replaces the launcher itself.
To keep your own code running as well, you need another process.

The [fork system call](https://man7.org/linux/man-pages/man2/fork.2.html) creates a child process.
Both processes continue immediately after the syscall, with their own copies of the program's memory.
The child's return value is zero; the parent's is the child's process ID (PID).
That difference lets the same program choose different work in each process.

On 64-bit x86 Linux, `fork` is syscall 57 and takes no arguments.
Print the prompt and read the pathname before creating the child.
Have the child execute the requested program.
Have the parent print `parent alive` followed by a newline, then exit with status 0.

The operating system can run either process first, so the parent message and the command's output may appear in either order.
If they use several writes, their output can also be interleaved.
The input limits and argument array are unchanged.

Build your executable and submit it with `/challenge/check shell`.
