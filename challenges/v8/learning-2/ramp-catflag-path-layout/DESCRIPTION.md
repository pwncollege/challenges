The capstone invokes `/challenge/catflag` through a process-control transfer, so the exploit needs the target path to be laid out in writable memory.
For `execve`, the path argument is a null-terminated C string: the path bytes followed by one zero byte.

In this level, the harness gives you an absolute-write-shaped scratch region as `api.scratchAddress`.
It also gives you the target string as `api.expectedPath` and `api.writeBytes(address, bytes)`.
Write the null-terminated `/challenge/catflag` string inside the scratch range and return `pathAddress`.
Run `/challenge/run` with your solve file to get the flag.
