The parent now survives long enough to print a message, but that message can appear before the command finishes.
A shell needs to know when a command is done before it gives control back to the person using it.

The [wait4 system call](https://man7.org/linux/man-pages/man2/wait4.2.html) lets a parent wait for a child to finish and collect it.
On 64-bit x86 Linux, it is syscall 61.
Its arguments are the child's PID, a status pointer, options, and a resource-usage pointer.
Use zero options for a blocking wait; both output pointers may be NULL because you do not need those results yet.
For Linux syscalls, the fourth argument uses `r10`, unlike the `rcx` used by the function calling convention.
A successful wait returns the PID it collected.

Keep the prompt, input, and child execution from the previous level.
The parent must now wait for that child, print `child finished` followed by a newline, and exit with status 0.
Its message must come after the command's output.

Build and submit with `/challenge/check shell`.
