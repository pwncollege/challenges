A pathname is enough to run a program, but most useful programs also need arguments.
Your calculator and formatter already consume them through `argv`.

Extend each external command to contain a pathname and one argument, separated by spaces or tabs.
The new program must receive the pathname as `argv[0]` and the argument as `argv[1]`.
Each entry points to its own NUL-terminated word, and a NULL pointer ends the array.

For example, `/usr/bin/echo hello` should run `echo` with the argument `hello`.
The entire input still fits in 255 bytes, including its newline.
The builtin remains just `exit`.

Build and submit with `/challenge/check shell`.
