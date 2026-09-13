Different programs need different numbers of arguments.
Replace the fixed count with a loop that builds `argv` from the words actually present.

Accept zero through eight arguments after the pathname, separated by spaces or tabs.
The pathname still goes first, each word is NUL-terminated, and the pointer array ends with NULL.
The whole input remains at most 255 bytes including its newline.
Successive commands can have different argument counts.

Keep execution, waiting, failure recovery, and `exit` working.
Build and submit your shell with `/challenge/check shell`.
