{% raw %}
class ASMLevel6(ASMBase):
    """
    Modulo
    """

    init_rax = 0xFFFFFFFFFFFFFFFF
    init_rdi = random.randint(1000000, 1000000000)
    init_rsi = 2 ** random.randint(2, 16) - 1

    registers_use = True
    dynamic_values = True

    @property
    def description(self):
        return f"""
        Modulo in assembly is another interesting concept!

        x86 allows you to get the remainder after a div operation.

        For instance: 10 / 3 -> remainder = 1

        The remainder is the same as modulo, which is also called the "mod" operator.

        In most programming languages we refer to mod with the symbol '%'.

        Please compute the following:
          rdi % rsi

        Place the value in rax.

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
          rsi = {hex(self.init_rsi)}
        """

    def trace(self):
        self.start()
        expected = self.init_rdi % self.init_rsi
        yield self.rax == expected, f"rax was expected to be {hex(expected)}, but instead was {hex(self.rax)}"
{% endraw %}
