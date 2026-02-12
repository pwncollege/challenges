{% raw %}
class ASMLevel23(ASMBase):
    """
    Do a:
    1. relative jump
    """

    CODE_ADDR = ASMBase.CODE_ADDR + random.randint(0x10, 0x100)

    init_rsp = ASMBase.RSP_INIT - 0x8
    init_mem_rsp = random.randint(0x10, 0x100)

    relative_offset = 0x51

    dynamic_values = True
    ip_control = True

    @property
    def init_memory(self):
        return {
            self.init_rsp: self.init_mem_rsp.to_bytes(8, "little"),
        }

    @property
    def description(self):
        return f"""
        Recall that for all jumps, there are three types:
          Relative jumps
          Absolute jumps
          Indirect jumps

        In this level we will ask you to do a relative jump.

        You will need to fill space in your code with something to make this relative jump possible.

        We suggest using the `nop` instruction. It's 1 byte long and very predictable.

        In fact, the as assembler that we're using has a handy .rept directive that you can use to
        repeat assembly instructions some number of times:
          https://ftp.gnu.org/old-gnu/Manuals/gas-2.9.1/html_chapter/as_7.html

        Useful instructions for this level:
          jmp (reg1 | addr | offset) ; nop

        Hint: for the relative jump, lookup how to use `labels` in x86.

        Using the above knowledge, perform the following:
          Make the first instruction in your code a jmp
          Make that jmp a relative jump to {hex(self.relative_offset)} bytes from the current position
          At the code location where the relative jump will redirect control flow set rax to 0x1

        We will now set the following in preparation for your code:
          Loading your given code at: {hex(self.CODE_ADDR)}
        """

    def trace(self):
        self.start()
        yield self.bb_trace[0] == self.CODE_ADDR, f"Expected code to start executing at {self.CODE_ADDR}"
        yield self.bb_trace[1] == self.CODE_ADDR + self.relative_offset + self.get_size_of_insn_at(0), f"Expected code to jump to {hex(self.CODE_ADDR + self.relative_offset + self.get_size_of_insn_at(0))}, but instead jumped to {hex(self.bb_trace[1])}"
        yield self.rax == 1, f"rax expected to be {hex(1)}, however was {hex(self.rax)}"
{% endraw %}
