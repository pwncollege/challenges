{% raw %}
class ASMLevel14(ASMBase):
    """
    Read and Write to memory
    """

    init_value = random.randint(1000000, 2000000)

    dynamic_values = True
    memory_use = True

    @property
    def init_memory(self):
        return {self.DATA_ADDR: self.init_value.to_bytes(8, "little")}

    @property
    def description(self):
        return f"""
        Please perform the following:
          Place the value stored at 0x404000 into rax
          Increment the value stored at the address 0x404000 by 0x1337

        Make sure the value in rax is the original value stored at 0x404000 and make sure
        that [0x404000] now has the incremented value.

        We will now set the following in preparation for your code:
          [0x404000] = {hex(self.init_value)}
        """

    def trace(self):
        self.start()
        yield self.rax == self.init_value, f"rax was expected to be {hex(self.init_value)}, but instead was {hex(self.rax)}"
        yield self[self.DATA_ADDR : self.DATA_ADDR + 8] == (self.init_value + 0x1337).to_bytes(8, "little"), f"[{hex(self.DATA_ADDR)}] expected to be {hex(self.init_value + 0x1337)}, instead has {hex(int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 8], 'little'))}"
{% endraw %}
