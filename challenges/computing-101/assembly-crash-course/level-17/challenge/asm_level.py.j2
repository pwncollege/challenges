{% raw %}
class ASMLevel24(ASMBase):
    """
    Jump to provided code:
    1. relative jump
    2. absolute jump
    """

    CODE_ADDR = ASMBase.CODE_ADDR + random.randint(0x10, 0x100)

    init_rsp = ASMBase.RSP_INIT - 0x8
    init_mem_rsp = random.randint(0x10, 0x100)

    relative_offset = 0x51
    library_code = f"""
        mov rsi, rdi
        mov rdi, {ASMBase.secret_key}
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
        Now, we will combine the two prior levels and perform the following:
          Create a two jump trampoline:
            Make the first instruction in your code a jmp
            Make that jmp a relative jump to {hex(self.relative_offset)} bytes from its current position
            At {hex(self.relative_offset)} write the following code:
              Place the top value on the stack into register rdi
              jmp to the absolute address {hex(self.LIB_ADDR)}

        We will now set the following in preparation for your code:
          Loading your given code at: {hex(self.CODE_ADDR)}
          (stack) [{hex(self.RSP_INIT - 0x8)}] = {hex(self.init_mem_rsp)}
        """

    def trace(self):
        self.start()
        # NOTE: The bb_trace checks are cursed and should be burnt to
        # the ground and redone. The key problem is that this
        # means that the student cannot put `int 3` as the
        # first instruction of the challenge (which kinda
        # breaks it). However, it's better than the prior
        # hardcoded 3 locations (as _any_ `int 3` would break
        # it).

        yield self.bb_trace[0] == self.CODE_ADDR, f"Expected code to start executing at {self.CODE_ADDR}"
        yield self.bb_trace[1] == self.CODE_ADDR + self.relative_offset + self.get_size_of_insn_at(0), f"Expected code to jump to {hex(self.CODE_ADDR + self.relative_offset + self.get_size_of_insn_at(0))}, but instead jumped to {hex(self.bb_trace[1])}"
        yield self.bb_trace[-1] == self.LIB_ADDR, f"Expected code to jump to {hex(self.LIB_ADDR)} at the end, but was {hex(self.bb_trace[-1])} instead"
        yield self.rdi == self.secret_key, f"rdi expected to be {hex(self.secret_key)}, but was {hex(self.rdi)} instead"
        yield self.rsi == self.init_mem_rsp, f"rsi expected to be {hex(self.init_mem_rsp)}, but was {hex(self.rsi)} instead"
{% endraw %}
