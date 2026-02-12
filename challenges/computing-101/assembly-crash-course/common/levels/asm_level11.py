{% raw %}
class ASMLevel11(ASMBase):
    """
    Hard Bit-Logic Level
    """

    init_rax = 0xFFFFFFFFFFFFFFFF
    init_rdi = random.randint(1000000, 1000000000)

    dynamic_values = True
    registers_use = True
    bit_logic = True
    whitelist = ["and", "xor", "or"]

    @property
    def description(self):
        return f"""
        Using only the following instructions:
          and, or, xor

        Implement the following logic:
          if x is even then
            y = 1
          else
            y = 0

        where:
          x = rdi
          y = rax

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
        """

    def trace(self):
        for i in range(100):
            self.create()
            self.start()
            expected = (self.init_rdi & 0x1) ^ 0x1
            yield self.rax == expected, f"rax was expected to be {hex(expected)}, but instead was {hex(self.rax)}"

    def create(self, *args, **kwargs):
        self.init_rdi = random.randint(1000000, 1000000000)
        super().create(*args, **kwargs)
{% endraw %}
