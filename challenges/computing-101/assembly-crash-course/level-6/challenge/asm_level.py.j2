{% raw %}
class ASMLevel8(ASMBase):
    """
    Small Register Access and mod
    """

    init_rdi = random.randint(0x0101, 0xFFFF)
    init_rsi = random.randint(0x01000001, 0xFFFFFFFF)

    registers_use = True
    dynamic_values = True
    whitelist = ["mov"]

    @property
    def description(self):
        return f"""
        It turns out that using the div operator to compute the modulo operation is slow!

        We can use a math trick to optimize the modulo operator (%). Compilers use this trick a lot.

        If we have "x % y", and y is a power of 2, such as 2^n, the result will be the lower n bits of x.

        Therefore, we can use the lower register byte access to efficiently implement modulo!

        Using only the following instruction(s):
          mov

        Please compute the following:
          rax = rdi % 256
          rbx = rsi % 65536

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
          rsi = {hex(self.init_rsi)}
        """

    def trace(self):
        self.start()
        yield (self.init_rdi % 256) == self.rax, f"rax was expected to be {hex(self.init_rdi % 256)}, but instead was {hex(self.rax)}"
        yield(self.init_rsi % 65536) == self.rbx, f"rbx was expected to be {hex(self.init_rsi % 65536)}, but instead was {hex(self.rbx)}"
{% endraw %}
