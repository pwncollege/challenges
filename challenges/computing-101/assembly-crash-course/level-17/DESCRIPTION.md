We will now set some values in memory dynamically before each run. On each run, the values will change. This means you will need to do some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it's `rax`.

In this level, you will be working with control flow manipulation. This involves using instructions to both indirectly and directly control the special register `rip`, the instruction pointer. You will use instructions such as `jmp`, `call`, `cmp`, and their alternatives to implement the requested behavior.

Now, we will combine the two prior levels and perform the following:

- Create a two jump trampoline:
  - Make the first instruction in your code a `jmp`.
  - Make that `jmp` a relative jump to 0x51 bytes from its current position.
  - At 0x51, write the following code:
    - Place the top value on the stack into register `rdi`.
    - `jmp` to the absolute address 0x403000.
