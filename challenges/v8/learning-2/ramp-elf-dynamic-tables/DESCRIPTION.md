The ELF dynamic table is a list of tag/value records used by the dynamic linker.
For this exploit, the useful records point to the string table, symbol table, and PLT relocation table that name imported functions.
The previous level found the dynamic-table range; this level only walks its records.

In this level, the harness gives you the provided loaded-ELF fixture's dynamic-table range as `api.dynamicAddress` and `api.dynamicSize`.
It also gives you `api.read64`, `api.ptrFromDynamicValue(value)`, and the needed dynamic-table constants.
Those constants are `api.DT_NULL`, `api.DT_STRTAB`, `api.DT_SYMTAB`, `api.DT_SYMENT`, `api.DT_JMPREL`, `api.DT_PLTRELSZ`, and `api.DT_RELAENT`.
Walk the dynamic records and return `strtab`, `symtab`, `syment`, `jmprel`, `pltrelsz`, and `relaent`.
Run `/challenge/run` with your solve file to get the flag.
