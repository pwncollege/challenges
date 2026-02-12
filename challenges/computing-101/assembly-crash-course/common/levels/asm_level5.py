{% raw %}
class ASMLevel5(ASMBase):
    """
    Integer Division
    """

    init_rdi = random.randint(1000, 10000)
    init_rsi = random.randint(10, 100)

    registers_use = True
    dynamic_values = True

    @property
    def description(self):
        return f"""
        Division in x86 is more special than in normal math. Math in here is
        called integer math. This means every value is a whole number.

        As an example: 10 / 3 = 3 in integer math.

        Why?

        Because 3.33 is rounded down to an integer.

        The relevant instructions for this level are:
          mov rax, reg1; div reg2

        Note: div is a special instruction that can divide
        a 128-bit dividend by a 64-bit divisor, while
        storing both the quotient and the remainder, using only one register as an operand.

        How does this complex div instruction work and operate on a
        128-bit dividend (which is twice as large as a register)?

        For the instruction: div reg, the following happens:
          rax = rdx:rax / reg
          rdx = remainder

        rdx:rax means that rdx will be the upper 64-bits of
        the 128-bit dividend and rax will be the lower 64-bits of the
        128-bit dividend.

        You must be careful about what is in rdx and rax before you call div.

        Please compute the following:
          speed = distance / time, where:
            distance = rdi
            time = rsi
            speed = rax

        Note that distance will be at most a 64-bit value, so rdx should be 0 when dividing.

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
          rsi = {hex(self.init_rsi)}
        """

    def trace(self):
        self.start()
        expected = self.init_rdi // self.init_rsi
        yield self.rax == expected, f"rax was expected to be {hex(expected)}, but instead was {hex(self.rax)}"
{% endraw %}
