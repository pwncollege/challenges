x86 stores every multi-byte value *little-endian* (low byte first), and that fact turns up everywhere you look at raw memory: hex dumps, debuggers, exploits.
To work properly in these contexts, you need to understand byte order.
This module makes it second nature.

You'll crack a series of programs that hide a password in their own compiled code, reading it back out of the disassembly at every size, whether it's a "qword", a lone byte, or a structure.
By the end, byte order won't trip you up in a hex dump, a debugger, or an exploit ever again (or we'll add more challenges to make it so!).
