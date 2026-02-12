{% raw %}
class ASMLevel15(ASMBase):
    """
    Reading just one byte from memory address
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
        Recall that registers in x86_64 are 64 bits wide, meaning they can store 64 bits.

        Similarly, each memory location can be treated as a 64 bit value.

        We refer to something that is 64 bits (8 bytes) as a quad word.

        Here is the breakdown of the names of memory sizes:
          Quad Word   = 8 Bytes = 64 bits
          Double Word = 4 bytes = 32 bits
          Word        = 2 bytes = 16 bits
          Byte        = 1 byte  = 8 bits

        In x86_64, you can access each of these sizes when dereferencing an address, just like using
        bigger or smaller register accesses:
          mov al, [address]        <=>        moves the least significant byte from address to rax
          mov ax, [address]        <=>        moves the least significant word from address to rax
          mov eax, [address]       <=>        moves the least significant double word from address to rax
          mov rax, [address]       <=>        moves the full quad word from address to rax

        Remember that moving into al does not fully clear the upper bytes.

        Please perform the following:
          Set rax to the byte at 0x404000

        We will now set the following in preparation for your code:
          [0x404000] = {hex(self.init_value)}
        """

    def trace(self):
        self.start()
        expected_value = self.init_value & 0xff
        yield self.rax == expected_value, f"rax expected to be {hex(expected_value)}, however was {hex(self.rax)}"
{% endraw %}
