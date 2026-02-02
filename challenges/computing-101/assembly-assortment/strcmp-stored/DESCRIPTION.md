So far, the values you've been reversing have been embedded directly in instructions as immediate operands.
However, this challenge compares the first program argument against a hardcoded string inside the challenge.
The string lives in a different section of the program file: the binary's `.rodata` (read-only data) section, rather than in the instructions themselves.

There are several options to find it:
- The most familiar: `stepi` to where the comparison is happening and `x` the registers pointing to the data.
- Use `strings /challenge/reverse-me` to list all printable strings in the binary. There are a lot, but one of them will be the password.
- Use `objdump -s -j .rodata /challenge/reverse-me` to dump the raw contents of the `.rodata` section.

Which you use is up to you!
