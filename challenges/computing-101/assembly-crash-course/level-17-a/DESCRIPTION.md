We will now set some values in memory dynamically before each run. On each run, the values will change. This means you will need to do some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it's `rax`.

In this level, you will be working with control flow manipulation. This involves using instructions to both indirectly and directly control the special register `rip`, the instruction pointer. You will use instructions such as `jmp`, `call`, `cmp`, and their alternatives to implement the requested behavior.

Earlier, you learned how to manipulate data in a pseudo-control way, but x86 gives us actual instructions to manipulate control flow directly.

There are two major ways to manipulate control flow:
- Through a jump
- Through a call

In this level, you will work with jumps.

There are two types of jumps:
- Unconditional jumps
- Conditional jumps

Unconditional jumps always trigger and are not based on the results of earlier instructions.

As you know, memory locations can store data and instructions. Your code will be stored at `0x400042` (this will change each run).

For all jumps, there are three types:
- Relative jumps: jump + or - the next instruction.
- Absolute jumps: jump to a specific address.
- Indirect jumps: jump to the memory address specified in a register.

In x86, absolute jumps (jump to a specific address) are accomplished by first loading the target address into a general-purpose register (we'll call this placeholder `reg`), then doing `jmp reg`.

In this level, we will ask you to do an absolute jump. Perform the following: Jump to the absolute address `0x403000`.
