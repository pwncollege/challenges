shellcode = mmap((void *){{ hex(challenge.shellcode_address) }}, {{ hex(challenge.allocation_size) }}, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_PRIVATE|MAP_ANON, 0, 0);
assert(shellcode == (void *){{ hex(challenge.shellcode_address) }});
printf("Mapped {{ hex(challenge.allocation_size) }} bytes for shellcode at %p!\n", shellcode);
