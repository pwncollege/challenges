We will now set some values in memory dynamically before each run. On each run, the values will change. This means you will need to perform some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it's `rax`.

In this level, you will be working with control flow manipulation. This involves using instructions to both indirectly and directly control the special register `rip`, the instruction pointer. You will use instructions such as `jmp`, `call`, `cmp`, and their alternatives to implement the requested behavior.

Recall that for all jumps, there are three types:

- Relative jumps
- Absolute jumps
- Indirect jumps

In this level, we will ask you to do a relative jump. You will need to fill space in your code with something to make this relative jump possible. We suggest using the `nop` instruction. It's 1 byte long and very predictable.

In fact, the assembler that we're using has a handy `.rept` directive that you can use to repeat assembly instructions some number of times: [GNU Assembler Manual](https://ftp.gnu.org/old-gnu/Manuals/gas-2.9.1/html_chapter/as_7.html)

Useful instructions for this level:

- `jmp (reg1 | addr | offset)`
- `nop`

Hint: For the relative jump, look up how to use `labels` in x86.

Using the above knowledge, perform the following:

- Make the first instruction in your code a `jmp`.
- Make that `jmp` a relative jump to 0x51 bytes from the current position.
- At the code location where the relative jump will redirect control flow, set `rax` to 0x1.
