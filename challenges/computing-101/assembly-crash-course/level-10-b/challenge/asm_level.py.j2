{% raw %}
class ASMLevel13(ASMBase):
    """
    Write to memory
    """

    init_rax = random.randint(1000000, 2000000)

    dynamic_values = True
    memory_use = True

    @property
    def description(self):
        return f"""
        Please perform the following:
          Place the value stored in rax to 0x404000

        We will now set the following in preparation for your code:
          rax = {hex(self.init_rax)}
        """

    def trace(self):
        self.start()
        yield self[self.DATA_ADDR : self.DATA_ADDR + 8] == (self.init_rax).to_bytes(8, "little"), f"[{hex(self.DATA_ADDR)}] expected to be {hex(self.init_rax)}, instead has {hex(int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 8], 'little'))}"
{% endraw %}
