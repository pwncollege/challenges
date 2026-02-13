{% raw %}
class ASMLevel7(ASMBase):
    """
    Small Register Access
    """

    # Make sure that ah part is always 0 no matter the random
    init_rax = random.randint(0xCAFED00D1337BEEF, 0xFAFED00D1337BEEF) & 0xFFFFFFFFFFFF00FF

    registers_use = True
    dynamic_values = True
    whitelist = ["mov"]

    def init(self):
        self.instruction_counts = defaultdict(int)

    @property
    def description(self):
        return f"""
        Another cool concept in x86 is the ability to independently access to lower register bytes.

        Each register in x86_64 is 64 bits in size, and in the previous levels we have accessed
        the full register using rax, rdi or rsi.

        We can also access the lower bytes of each register using different register names.

        For example the lower 32 bits of rax can be accessed using eax, the lower 16 bits using ax,
        the lower 8 bits using al.

        MSB                                    LSB
        +----------------------------------------+
        |                   rax                  |
        +--------------------+-------------------+
                             |        eax        |
                             +---------+---------+
                                       |   ax    |
                                       +----+----+
                                       | ah | al |
                                       +----+----+

        Lower register bytes access is applicable to almost all registers.

        Using only one move instruction, please set the upper 8 bits of the ax register to 0x42.

        We will now set the following in preparation for your code:
          rax = {hex(self.init_rax)}
        """

    def code_hook(self, uc, address, size, user_data):
        super().code_hook(uc, address, size, user_data)
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        instruction = next(md.disasm(uc.mem_read(address, size), address))
        self.instruction_counts[instruction.mnemonic] += 1

    def trace(self):
        self.start()
        mov_count = self.instruction_counts["mov"]
        yield mov_count == 1, f"Can only use 1 mov, instead used {mov_count}"

        expected_rax = self.init_rax ^ 0x4200
        yield (expected_rax) == self.rax, f"ah was expected to be {hex(0x42)}, but instead was {hex(self.rax>>8 & 0xFF)}"
{% endraw %}
