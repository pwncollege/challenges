{% raw %}
class ASMLevel26(ASMBase):
    multi_test = True
    ip_control = True
    libraries_code = [
          f"""
          mov rsi, rdi
          mov rdi, {ASMBase.secret_key + i}
          mov rax, 0x3c
          syscall
          """
          for i in range(5)
    ]

    def __init__(self, *args, **kwargs):
        self.libraries = [
          pwnlib.asm.asm(library_code)
          for library_code in self.libraries_code
        ]
        super().__init__(*args, **kwargs)

    def init(self):
        self.jump_locations = [
            random.randint(self.LIB_ADDR + (200 * i), self.LIB_ADDR + (200 * i) + 100)
            for i in range(5)
        ]

        self.init_rdi = random.randint(0, 5)
        self.init_rsi = self.DATA_ADDR + random.randint(0, 1024)

        self.init_memory = {
            self.init_rsi: b"".join(
                location.to_bytes(8, "little") for location in self.jump_locations
            ),
            **{
                location: library
                for location, library in zip(self.jump_locations, self.libraries)
            },
        }

        self.instruction_counts = defaultdict(int)

    @property
    def description(self):
        return f"""
        The last jump type is the indirect jump, which is often used for switch statements in the real world.

        Switch statements are a special case of if-statements that use only numbers to determine where the control flow will go.

        Here is an example:
          switch(number):
            0: jmp do_thing_0
            1: jmp do_thing_1
            2: jmp do_thing_2
            default: jmp do_default_thing

        The switch in this example is working on `number`, which can either be 0, 1, or 2.

        In the case that `number` is not one of those numbers, the default triggers.

        You can consider this a reduced else-if type structure.

        In x86, you are already used to using numbers, so it should be no surprise that you can make if statements based on something being an exact number.

        In addition, if you know the range of the numbers, a switch statement works very well.

        Take for instance the existence of a jump table.

        A jump table is a contiguous section of memory that holds addresses of places to jump.

        In the above example, the jump table could look like:
          [0x1337] = address of do_thing_0
          [0x1337+0x8] = address of do_thing_1
          [0x1337+0x10] = address of do_thing_2
          [0x1337+0x18] = address of do_default_thing

        Using the jump table, we can greatly reduce the amount of cmps we use.

        Now all we need to check is if `number` is greater than 2.

        If it is, always do:
          jmp [0x1337+0x18]
        Otherwise:
          jmp [jump_table_address + number * 8]

        Using the above knowledge, implement the following logic:
          if rdi is 0:
            jmp {hex(self.jump_locations[0])}
          else if rdi is 1:
            jmp {hex(self.jump_locations[1])}
          else if rdi is 2:
            jmp {hex(self.jump_locations[2])}
          else if rdi is 3:
            jmp {hex(self.jump_locations[3])}
          else:
            jmp {hex(self.jump_locations[4])}

        Please do the above with the following constraints:
          Assume rdi will NOT be negative
          Use no more than 1 cmp instruction
          Use no more than 3 jumps (of any variant)
          We will provide you with the number to 'switch' on in rdi.
          We will provide you with a jump table base address in rsi.

        Here is an example table:
          [{hex(self.init_rsi + 0)}] = {hex(self.jump_locations[0])} (addrs will change)
          [{hex(self.init_rsi + 8)}] = {hex(self.jump_locations[1])}
          [{hex(self.init_rsi + 16)}] = {hex(self.jump_locations[2])}
          [{hex(self.init_rsi + 24)}] = {hex(self.jump_locations[3])}
          [{hex(self.init_rsi + 32)}] = {hex(self.jump_locations[4])}
        """

    def code_hook(self, uc, address, size, user_data):
        super().code_hook(uc, address, size, user_data)
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        instruction = next(md.disasm(uc.mem_read(address, size), address))
        self.instruction_counts[instruction.mnemonic] += 1

    def trace(self):
        for i in range(100):
            self.create()
            self.start()
            jmps = sum(
                count
                for instruction, count in self.instruction_counts.items()
                if instruction.startswith("j")
            )
            cmps = self.instruction_counts["cmp"]
            yield jmps <= 3, f"In attempt {i+1}, used {jmps} jumps which is too many"
            yield cmps <= 1, f"In attempt {i+1}, used {cmps} cmp instructions which is too many"
            yield self.rdi == min(self.init_rdi, 4) + self.secret_key, f"In attempt {i+1}, rdi was expected to be {hex(min(self.init_rdi, 4) + self.secret_key)}, but was {hex(self.rdi)} instead"
            if (i+1) % 10 == 0:
                print(f"Completed test {i+1}")
{% endraw %}
