{% raw %}
class ASMLevel10(ASMBase):
    """
    Logic gates as a mov (bit logic)
    """

    init_rax = 0xFFFFFFFFFFFFFFFF
    init_rdi = random.randint(0x55AA55AA55AA55AA, 0x99BB99BB99BB99BB)
    init_rsi = random.randint(0x55AA55AA55AA55AA, 0x99BB99BB99BB99BB)

    dynamic_values = True
    registers_use = True
    bit_logic = True
    blacklist = ["mov", "xchg"]

    @property
    def description(self):
        return f"""
        Bitwise logic in assembly is yet another interesting concept!
        x86 allows you to perform logic operations bit by bit on registers.

        For the sake of this example say registers only store 8 bits.

        The values in rax and rbx are:
          rax = 10101010
          rbx = 00110011

        If we were to perform a bitwise AND of rax and rbx using the
        "and rax, rbx" instruction, the result would be calculated by
        ANDing each bit pair 1 by 1 hence why it's called a bitwise
        logic.

        So from left to right:
          1 AND 0 = 0
          0 AND 0 = 0
          1 AND 1 = 1
          0 AND 1 = 0
          ...

        Finally we combine the results together to get:
          rax = 00100010

        Here are some truth tables for reference:
              AND          OR           XOR
           A | B | X    A | B | X    A | B | X
          ---+---+---  ---+---+---  ---+---+---
           0 | 0 | 0    0 | 0 | 0    0 | 0 | 0
           0 | 1 | 0    0 | 1 | 1    0 | 1 | 1
           1 | 0 | 0    1 | 0 | 1    1 | 0 | 1
           1 | 1 | 1    1 | 1 | 1    1 | 1 | 0

        Without using the following instructions:
          mov, xchg

        Please perform the following:
          rax = rdi AND rsi

        i.e. Set rax to the value of (rdi AND rsi)

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
          rsi = {hex(self.init_rsi)}
        """

    def trace(self):
        self.start()
        expected = self.init_rdi & self.init_rsi
        yield self.rax == expected, f"rax was expected to be {hex(expected)}, but instead was {hex(self.rax)}"
{% endraw %}
