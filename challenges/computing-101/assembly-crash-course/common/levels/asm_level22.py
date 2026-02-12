{% raw %}
class ASMLevel22(ASMBase):
    """
    Jump to provided code with absolute jump
    """

    CODE_ADDR = ASMBase.CODE_ADDR + random.randint(0x10, 0x100)

    init_rsp = ASMBase.RSP_INIT - 0x8
    init_mem_rsp = random.randint(0x10, 0x100)

    relative_offset = 0x51
    library_code = f"""
        mov rax, 0x3c
        syscall
        """

    dynamic_values = True
    ip_control = True

    def __init__(self, *args, **kwargs):
        self.library = pwnlib.asm.asm(self.library_code)
        super().__init__(*args, **kwargs)

    @property
    def init_memory(self):
        return {
            self.init_rsp: self.init_mem_rsp.to_bytes(8, "little"),
            self.LIB_ADDR: self.library,
        }

    @property
    def description(self):
        return f"""
        Earlier, you learned how to manipulate data in a pseudo-control way, but x86 gives us actual
        instructions to manipulate control flow directly.

        There are two major ways to manipulate control flow:
         through a jump;
         through a call.

        In this level, you will work with jumps.

        There are two types of jumps:
          Unconditional jumps
          Conditional jumps

        Unconditional jumps always trigger and are not based on the results of earlier instructions.

        As you know, memory locations can store data and instructions.

        Your code will be stored at {hex(self.CODE_ADDR)} (this will change each run).

        For all jumps, there are three types:
          Relative jumps: jump + or - the next instruction.
          Absolute jumps: jump to a specific address.
          Indirect jumps: jump to the memory address specified in a register.

        In x86, absolute jumps (jump to a specific address) are accomplished by first putting the target address in a register reg, then doing jmp reg.

        In this level we will ask you to do an absolute jump.

        Perform the following:
          Jump to the absolute address {hex(self.LIB_ADDR)}

        We will now set the following in preparation for your code:
          Loading your given code at: {hex(self.CODE_ADDR)}
        """

    def trace(self):
        self.start()
        yield self.bb_trace[0] == self.CODE_ADDR, f"Expected code to start executing at {self.CODE_ADDR}"
        yield self.bb_trace[-1] == self.LIB_ADDR, f"Expected code to jump to {hex(self.LIB_ADDR)} at the end, but was {hex(self.bb_trace[-1])} instead"
{% endraw %}
