So far, every requested executable has existed.
A mistyped pathname changes what happens after `execve`: the syscall returns to your code with a negative error number instead of replacing the process.

Extend your shell to handle that return.
For a failed execution, write `exec failed` followed by a newline to standard error, then end the child with a nonzero exit status.
The parent must finish waiting and accept the next command.

The checker will place a nonexistent pathname between valid commands.
Build and submit with `/challenge/check shell`.
