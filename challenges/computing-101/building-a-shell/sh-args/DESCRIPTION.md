Now accept exactly three arguments after each external command's pathname.
Keep them in order in `argv`, with the pathname first and the terminating NULL pointer after the last argument.

For example, `/usr/bin/echo one two three` should print `one two three` and a newline.
Spaces and tabs separate words, and the whole input still fits in 255 bytes including the newline.
The builtin remains just `exit`.

Extend your shell and submit it with `/challenge/check shell`.
