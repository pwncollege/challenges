The capstone now has the `/challenge/catflag` path string in writable memory.
For `execve`, `argv` is a pointer array ending with a null pointer: `argv[0]` points at the path string and `argv[1]` is `NULL`.

In this level, the harness gives you the existing path pointer as `api.pathAddress`.
It also gives you an absolute-write-shaped scratch region as `api.scratchAddress` and `api.write64(address, value)`.
Write the two-qword `argv` array inside the scratch range, return `argvAddress`, then run `/challenge/run` with your solve file to get the flag.
