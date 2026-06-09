x86 stores every multi-byte value *little-endian* --- low byte first --- and that one fact turns up everywhere you look at raw memory: hex dumps, debuggers, exploits.

This module makes it second nature.
You'll crack a series of programs that hide a password in their own compiled code, reading it back out of the disassembly at every size --- qword, dword, word, and a lone byte --- and finally out of a struct that mixes them all.
Along the way you'll watch exactly which bytes flip and which don't (and find that a single byte never does).

By the end, byte order won't trip you up in a hex dump, a debugger, or an exploit again.
