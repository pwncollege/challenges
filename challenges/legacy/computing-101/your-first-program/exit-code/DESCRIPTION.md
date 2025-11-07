As you might know, every program exits with an _exit code_ as it terminates.
This is done by passing a parameter to the `exit` system call.

Similarly to how a system call number (e.g., `60` for `exit`) is specified in the `rax` variable, parameters are also passed to the syscall through registers.
System calls can take multiple parameters, though `exit` takes only one: the exit code.
The first parameter to a system call is passed via another register: `rdi`.
`rdi` is what we will focus on in this challenge.

In this challenge, you must make your program exit with the exit code of `42`.
Thus, your program will need three instructions:

1. Set your program's exit code (move it into `rdi`).
2. Set the system call number of the `exit` syscall (`mov rax, 60`).
3. `syscall`!

Now, go and do it!
