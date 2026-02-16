We will now set some values in memory dynamically before each run. On each run, the values will change. This means you will need to do some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it's `rax`.

In this level, you will be working with the stack, the memory region that dynamically expands and shrinks. You will be required to read and write to the stack, which may require you to use the `pop` and `push` instructions. You may also need to use the stack pointer register (`rsp`) to know where the stack is pointing.

In the previous levels, you used `push` and `pop` to store and load data from the stack. However, you can also access the stack directly using the stack pointer.

On x86, the stack pointer is stored in the special register, `rsp`. `rsp` always stores the memory address of the top of the stack, i.e., the memory address of the last value pushed.

Similar to the memory levels, we can use `[rsp]` to access the value at the memory address in `rsp`.

Without using `pop`, please calculate the average of 4 consecutive quad words stored on the stack. Push the average on the stack.

Hint:
- `RSP+0x??` Quad Word A
- `RSP+0x??` Quad Word B
- `RSP+0x??` Quad Word C
- `RSP`      Quad Word D
