We will now set some values in memory dynamically before each run. On each run, the values will change. This means you will need to perform some type of formulaic operation with registers. We will tell you which registers are set beforehand and where you should put the result. In most cases, it's `rax`.

In this level, you will be working with control flow manipulation. This involves using instructions to both indirectly and directly control the special register `rip`, the instruction pointer. You will use instructions such as `jmp`, `call`, `cmp`, and their alternatives to implement the requested behavior.

Recall that for all jumps, there are three types:

- Relative jumps: jump a certain number of bytes forward or backward from the current instruction.
- Absolute jumps: jump to a fixed memory address.
- Indirect jumps: jump to the address stored in a register or memory location.

Here, we are focusing on relative jumps. This means you will tell the CPU to “jump forward a certain number of bytes from where you are currently executing.” This is useful because your code can move in memory and the jump will still reach the correct target.

To implement a relative jump, you will need a few tools:
* `labels`: Instead of calculating addresses manually, you can use labels as placeholders. The assembler will automatically calculate the offset from your jump instruction to the label.
* `nop` (No Operation): A single-byte instruction that does nothing. It is predictable in size and can be used as filler to create an exact distance for your jump.
* `.rept` (Repeat Directive): A directive that tells the assembler to repeat a given instruction multiple times: [GNU Assembler Manual](https://ftp.gnu.org/old-gnu/Manuals/gas-2.9.1/html_chapter/as_7.html) This is perfect for generating a block of `nop` instructions without typing each one individually.

Please perform the following:
* Make the first instruction in your code a `jmp`.
* Make that `jmp` a relative jump of exactly 0x51 bytes from the current instruction.
* Fill the space between the jump and the destination with `nop` instructions using `.rept`.
* At the label where the relative jump lands, set `rax` to 0x1.

When your code runs, the CPU will execute the jump, skip over all the nop instructions, and continue at the instruction that sets `rax`. This will demonstrate how to control the flow of execution using relative jumps.
