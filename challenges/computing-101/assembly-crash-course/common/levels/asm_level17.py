{% raw %}
class ASMLevel17(ASMBase):
    """
    Write static values to dynamic memory (of different size)
    """

    init_rdi = ASMBase.DATA_ADDR + (8 * random.randint(0, 250))
    init_rsi = ASMBase.DATA_ADDR + (8 * random.randint(250, 500))

    target_mem_rdi = 0xDEADBEEF00001337
    target_mem_rsi = 0x000000C0FFEE0000

    interrupt_memory_read_base = [init_rdi, init_rsi]

    dynamic_values = True
    memory_use = True

    @property
    def init_memory(self):
        return {self.init_rdi: b"\xff" * 8, self.init_rsi: b"\xff" * 8}

    @property
    def description(self):
        return f"""
        It is worth noting, as you may have noticed, that values are stored in reverse order of how we
        represent them.

        As an example, say:
          [0x1330] = 0x00000000deadc0de

        If you examined how it actually looked in memory, you would see:
          [0x1330] = 0xde
          [0x1331] = 0xc0
          [0x1332] = 0xad
          [0x1333] = 0xde
          [0x1334] = 0x00
          [0x1335] = 0x00
          [0x1336] = 0x00
          [0x1337] = 0x00

        This format of storing things in 'reverse' is intentional in x86, and its called "Little Endian".

        For this challenge we will give you two addresses created dynamically each run.

        The first address will be placed in rdi.
        The second will be placed in rsi.

        Using the earlier mentioned info, perform the following:
          Set [rdi] = {hex(self.target_mem_rdi)}
          Set [rsi] = {hex(self.target_mem_rsi)}

        Hint: it may require some tricks to assign a big constant to a dereferenced register.
        Try setting a register to the constant value then assigning that register to the dereferenced register.

        We will now set the following in preparation for your code:
          [{hex(self.init_rdi)}] = 0xffffffffffffffff
          [{hex(self.init_rsi)}] = 0xffffffffffffffff
          rdi = {hex(self.init_rdi)}
          rsi = {hex(self.init_rsi)}
        """

    def trace(self):
        self.start()
        yield self[self.init_rdi : self.init_rdi + 8] == self.target_mem_rdi.to_bytes(8, "little"), f"[{hex(self.init_rdi)}] expected to be {hex(self.target_mem_rdi)}, instead was {hex(int.from_bytes(self[self.init_rdi : self.init_rdi + 8], 'little'))}"
        yield self[self.init_rsi : self.init_rsi + 8] == self.target_mem_rsi.to_bytes(8, "little"), f"[{hex(self.init_rsi)}] expected to be {hex(self.target_mem_rsi)}, instead was {hex(int.from_bytes(self[self.init_rsi : self.init_rsi + 8], 'little'))}"
{% endraw %}
