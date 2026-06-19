After an exploit resolves imported function targets, it still needs small instruction sequences to place syscall arguments.
On 64-bit x86, useful ROP gadgets are short byte patterns ending in `ret`.
The capstones use a plain `ret` for stack alignment and one multi-pop gadget that loads the argument registers for `syscall`.
The segment bounds and byte patterns are already known here; this level only teaches scanning executable bytes for those gadgets.

In this level, the harness gives you the provided loaded-ELF fixture's executable segment as `api.execStart` and `api.execSize`.
It also gives you the gadget byte patterns in `api.patterns` and the read helpers `api.read8`/`api.read64`.
Scan the executable segment and return `popArgs` and `ret`.
Run `/challenge/run` with your solve file to get the flag.
