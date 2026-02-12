{% raw %}
class ASMLevel3(ASMBase):
    """
    Modify registers
    """

    init_rdi = random.randint(0, 0x1000)

    registers_use = True
    dynamic_values = True

    @property
    def description(self):
        return f"""
        Many instructions exist in x86 that allow you to do all the normal
        math operations on registers and memory.

        For shorthand, when we say A += B, it really means A = A + B.

        Here are some useful instructions:
          add reg1, reg2       <=>     reg1 += reg2
          sub reg1, reg2       <=>     reg1 -= reg2
          imul reg1, reg2      <=>     reg1 *= reg2

        div is more complicated and we will discuss it later.
        Note: all 'regX' can be replaced by a constant or memory location

        Do the following:
          add 0x331337 to rdi

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
        """

    def trace(self):
        self.start()
        expected = self.init_rdi + 0x331337
        yield self.rdi == expected, f"rdi was expected to be {hex(expected)}, but instead was {hex(self.rdi)}"
{% endraw %}
