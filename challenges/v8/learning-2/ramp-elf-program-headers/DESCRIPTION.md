Once an exploit can read a loaded ELF image, it needs stable regions inside that image.
The ELF header points to a program-header table, and that table describes the loaded executable segment, writable segment, and dynamic table.
This ramp uses a deterministic loaded-ELF fixture so the parser is the only new concept.

In this level, the harness gives you the base address of the provided loaded-ELF fixture as `api.baseAddress`.
It also gives you `api.read16`, `api.read32`, `api.read64`, and the relevant program-header constants.
Those constants are `api.PT_LOAD`, `api.PT_DYNAMIC`, `api.PF_X`, and `api.PF_W`.
Walk the ELF program headers and return `execStart`, `execSize`, `writeStart`, `writeSize`, `dynamicAddress`, and `dynamicSize`.
Run `/challenge/run` with your solve file to get the flag.
