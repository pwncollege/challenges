{% raw %}
class ASMLevel4(ASMBase):
    """
    Reg complex use: calculate y = mx + b
    """

    init_rdi = random.randint(0, 10000)
    init_rsi = random.randint(0, 10000)
    init_rdx = random.randint(0, 10000)

    registers_use = True
    dynamic_values = True

    @property
    def description(self):
        return f"""
        Using your new knowledge, please compute the following:
          f(x) = mx + b, where:
            m = rdi
            x = rsi
            b = rdx

        Place the result into rax.

        Note: there is an important difference between mul (unsigned
        multiply) and imul (signed multiply) in terms of which
        registers are used. Look at the documentation on these
        instructions to see the difference.

        In this case, you will want to use imul.

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
          rsi = {hex(self.init_rsi)}
          rdx = {hex(self.init_rdx)}
        """

    def trace(self):
        self.start()
        expected = (self.init_rdi * self.init_rsi) + self.init_rdx
        yield self.rax == expected, f"rax was expected to be {hex(expected)}, but instead was {hex(self.rax)}"
{% endraw %}
