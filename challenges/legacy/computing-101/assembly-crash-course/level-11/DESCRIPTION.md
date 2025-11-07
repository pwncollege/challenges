We will now set some values in memory dynamically before each run. On each run, the values will change. This means you will need to perform some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it's `rax`.

In this level, you will be working with memory. This will require you to read or write to things stored linearly in memory. If you are confused, refer to the linear addressing module in 'ike. You may also be asked to dereference things, possibly multiple times, to things we dynamically put in memory for your use.

Recall the following:

- The breakdown of the names of memory sizes:
  - Quad Word = 8 Bytes = 64 bits
  - Double Word = 4 bytes = 32 bits
  - Word = 2 bytes = 16 bits
  - Byte = 1 byte = 8 bits

In x86_64, you can access each of these sizes when dereferencing an address, just like using bigger or smaller register accesses:

- `mov al, [address]` <=> moves the least significant byte from address to `rax`
- `mov ax, [address]` <=> moves the least significant word from address to `rax`
- `mov eax, [address]` <=> moves the least significant double word from address to `rax`
- `mov rax, [address]` <=> moves the full quad word from address to `rax`

Please perform the following:

- Set `rax` to the byte at `0x404000`
- Set `rbx` to the word at `0x404000`
- Set `rcx` to the double word at `0x404000`
- Set `rdx` to the quad word at `0x404000`
