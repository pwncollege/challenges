PLT relocation records connect imported function names to writable GOT slots.
Each relocation points at a symbol-table entry, and that symbol entry points into the string table for the imported name.
The dynamic-table walk is already done here; this level only resolves imported names from relocation records.

In this level, the harness gives you the provided loaded-ELF fixture's string table as `api.strtab`, symbol table as `api.symtab`, and PLT relocation table as `api.jmprel`.
It also gives you `api.syment`, `api.relaent`, `api.pltrelsz`, `api.read32`, `api.read64`, and `api.readCString`.
Use `api.baseAddress` when a relocation target is still base-relative.
Resolve the `syscall` and `exit` imports and return `syscallGot`, `exitGot`, `syscallTarget`, and `exitTarget`.
Run `/challenge/run` with your solve file to get the flag.
