Corrupted dispatch metadata can become a process-memory read/write primitive after the exploit wraps it cleanly.
That wrapper is the bridge from a one-off corruption shape to repeatable absolute memory access.

In this level, the harness gives you low-level dispatch read and write functions.
Return an object with `read32` and `write32` methods for absolute addresses, then run `/challenge/run` with your solve file to get the flag.
