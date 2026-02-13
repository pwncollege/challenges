{% raw %}
class ASMLevel18(ASMBase):
    """
    Write to dynamic address, consecutive
    """

    init_rdi = ASMBase.DATA_ADDR + (8 * random.randint(50, 100))
    init_rsi = ASMBase.DATA_ADDR + (8 * random.randint(200, 250))

    init_mem_rdi = random.randint(1000, 1000000)
    init_mem_rdi_next = random.randint(1000, 1000000)

    interrupt_memory_read_base = [init_rdi, init_rsi]

    dynamic_values = True
    memory_use = True

    @property
    def init_memory(self):
        return {
            self.init_rdi: self.init_mem_rdi.to_bytes(8, "little"),
            self.init_rdi + 8: self.init_mem_rdi_next.to_bytes(8, "little"),
        }

    @property
    def description(self):
        return f"""
        Recall that memory is stored linearly.

        What does that mean?

        Say we access the quad word at 0x1337:
          [0x1337] = 0x00000000deadbeef

        The real way memory is laid out is byte by byte, little endian:
          [0x1337] = 0xef
          [0x1337 + 1] = 0xbe
          [0x1337 + 2] = 0xad
          ...
          [0x1337 + 7] = 0x00

        What does this do for us?

        Well, it means that we can access things next to each other using offsets,
        similar to what was shown above.

        Say you want the 5th *byte* from an address, you can access it like:
          mov al, [address+4]

        Remember, offsets start at 0.

        Perform the following:
          Load two consecutive quad words from the address stored in rdi
          Calculate the sum of the previous steps quad words.
          Store the sum at the address in rsi

        We will now set the following in preparation for your code:
          [{hex(self.init_rdi)}] = {hex(self.init_mem_rdi)}
          [{hex(self.init_rdi + 8)}] = {hex(self.init_mem_rdi_next)}
          rdi = {hex(self.init_rdi)}
          rsi = {hex(self.init_rsi)}
        """

    def trace(self):
        self.start()
        yield self[self.init_rsi : self.init_rsi + 8] == (self.init_mem_rdi + self.init_mem_rdi_next).to_bytes(8, "little"), f"[{hex(self.init_rsi)}] expected to be {hex(self.init_mem_rdi + self.init_mem_rdi_next)}, but was {hex(int.from_bytes(self[self.init_rsi : self.init_rsi + 8], 'little'))} instead"
{% endraw %}
