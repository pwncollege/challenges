After the 32-bit fixture access is wrapped into qword reads, the exploit has a 64-bit absolute read shape.
A full exploit needs smaller reads too: ELF headers, relocation records, strings, and instruction scans all mix byte, halfword, word, and qword fields.
This level keeps the primitive fixed and teaches only the sub-qword read wrappers.

In this level, the harness provides only `api.read64(address)`.
Return `read8`, `read16`, and `read32` helpers that read little-endian unsigned values from provided loaded-ELF fixture addresses, including unaligned addresses.
Run `/challenge/run` with your solve file to get the flag.
