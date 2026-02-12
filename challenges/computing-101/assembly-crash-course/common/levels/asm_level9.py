{% raw %}
class ASMLevel9(ASMBase):
    """
    Shift
    """

    init_rdi = random.randint(0x55AA55AA55AA55AA, 0x99BB99BB99BB99BB)

    dynamic_values = True
    registers_use = True
    bit_logic = True
    whitelist = ["mov", "shr", "shl"]

    @property
    def description(self):
        return f"""
        Shifting bits around in assembly is another interesting concept!

        x86 allows you to 'shift' bits around in a register.

        Take, for instance, al, the lowest 8 bits of rax.

        The value in al (in bits) is:
          rax = 10001010

        If we shift once to the left using the shl instruction:
          shl al, 1

        The new value is:
          al = 00010100

        Everything shifted to the left and the highest bit fell off
        while a new 0 was added to the right side.

        You can use this to do special things to the bits you care about.

        Shifting has the nice side affect of doing quick multiplication (by 2)
        or division (by 2), and can also be used to compute modulo.

        Here are the important instructions:
          shl reg1, reg2       <=>     Shift reg1 left by the amount in reg2
          shr reg1, reg2       <=>     Shift reg1 right by the amount in reg2
          Note: 'reg2' can be replaced by a constant or memory location

        Using only the following instructions:
          mov, shr, shl

        Please perform the following:
          Set rax to the 5th least significant byte of rdi.

        For example:
          rdi = | B7 | B6 | B5 | B4 | B3 | B2 | B1 | B0 |
          Set rax to the value of B4

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
        """

    def trace(self):
        self.start()
        expected = (self.init_rdi >> 32) & 0xFF
        yield self.rax == expected, f"rax was expected to be {hex(expected)}, but instead was {hex(self.rax)}"
{% endraw %}
