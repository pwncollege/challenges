{% raw %}
class ASMLevel19(ASMBase):
    """
    Pop, Modify, Push
    """

    init_rdi = random.randint(10, 100000)
    init_rsp = ASMBase.RSP_INIT - 0x8
    init_mem_rsp = random.randint(1000000, 1000000000)

    dynamic_values = True
    stack_use = True

    def init(self):
        self.instruction_counts = defaultdict(int)

    @property
    def init_memory(self):
        return {self.init_rsp: self.init_mem_rsp.to_bytes(8, "little")}

    @property
    def description(self):
        return f"""
        In these levels we are going to introduce the stack.

        The stack is a region of memory that can store values for later.

        To store a value on the stack we use the push instruction, and to retrieve a value we use pop.

        The stack is a last in first out (LIFO) memory structure, and this means
        the last value pushed in the first value popped.

        Imagine unloading plates from the dishwasher let's say there are 1 red, 1 green, and 1 blue.
        First we place the red one in the cabinet, then the green on top of the red, then the blue.

        Our stack of plates would look like:
          Top ----> Blue
                    Green
          Bottom -> Red

        Now, if we wanted a plate to make a sandwich we would retrieve the top plate from the stack
        which would be the blue one that was last into the cabinet, ergo the first one out.

        On x86, the pop instruction will take the value from the top of the stack and put it into a register.

        Similarly, the push instruction will take the value in a register and push it onto the top of the stack.

        Using these instructions, take the top value of the stack, subtract rdi from it, then put it back.

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
          (stack) [{hex(self.init_rsp)}] = {hex(self.init_mem_rsp)}
        """

    def code_hook(self, uc, address, size, user_data):
        super().code_hook(uc, address, size, user_data)
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        instruction = next(md.disasm(uc.mem_read(address, size), address))
        self.instruction_counts[instruction.mnemonic] += 1


    def trace(self):
        self.start()
        push_count = self.instruction_counts["push"]
        pop_count = self.instruction_counts["pop"]

        yield pop_count > 0, f"Use at least one pop instruction"
        yield push_count > 0, f"Use at least one push instruction"
        yield self[self.init_rsp : self.init_rsp + 8] == (self.init_mem_rsp - self.init_rdi).to_bytes(8, "little"), f"[{hex(self.init_rsp)}] expected to be {hex(self.init_mem_rsp - self.init_rdi)}, but was {hex(int.from_bytes(self[self.init_rsp : self.init_rsp + 8], 'little'))} instead"
{% endraw %}
