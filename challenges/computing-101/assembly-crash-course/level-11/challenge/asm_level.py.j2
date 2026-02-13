{% raw %}
class ASMLevel16(ASMBase):
    """
    Reading specific sizes from addresses
    """

    init_value = random.randint(0x8000000000000000, 0x8FFFFFFFFFFFFFFF)

    dynamic_values = True
    memory_use = True

    @property
    def init_memory(self):
        return {self.DATA_ADDR: self.init_value.to_bytes(8, "little")}

    @property
    def description(self):
        return f"""
        Recall the following:
          The breakdown of the names of memory sizes:
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

        Please perform the following:
          Set rax to the byte at 0x404000
          Set rbx to the word at 0x404000
          Set rcx to the double word at 0x404000
          Set rdx to the quad word at 0x404000

        We will now set the following in preparation for your code:
          [0x404000] = {hex(self.init_value)}
        """

    def trace(self):
        self.start()
        yield self.rax == int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 1], "little"), f"rax expected to be {hex(int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 1], 'little'))}, however was {hex(self.rax)}"
        yield self.rbx == int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 2], "little"), f"rbx expected to be {hex(int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 2], 'little'))}, however was {hex(self.rbx)}"
        yield self.rcx == int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 4], "little"), f"rcx expected to be {hex(int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 4], 'little'))}, however was {hex(self.rcx)}"
        yield self.rdx == int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 8], "little"), f"rdx expected to be {hex(int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 8], 'little'))}, however was {hex(self.rdx)}"
{% endraw %}
