{% raw %}
class ASMLevel21(ASMBase):
    """
    R/W from stack without pop
    """

    init_rsp = ASMBase.RSP_INIT - 0x20
    init_mem_stack = [random.randint(1000000, 1000000000) for _ in range(4)]

    dynamic_values = True
    stack_use = True
    blacklist = ["pop"]

    @property
    def init_memory(self):
        return {
            self.init_rsp + (8 * i): value.to_bytes(8, "little")
            for i, value in enumerate(self.init_mem_stack)
        }

    @property
    def description(self):
        return f"""
        In the previous levels you used push and pop to store and load data from the stack.

        However you can also access the stack directly using the stack pointer.

        On x86, the stack pointer is stored in the special register, rsp.
        rsp always stores the memory address of the top of the stack,
        i.e. the memory address of the last value pushed.

        Similar to the memory levels, we can use [rsp] to access the value at the memory address in rsp.

        Without using pop, please calculate the average of 4 consecutive quad words stored on the stack.

        Push the average on the stack.

        Hint:
          RSP+0x?? Quad Word A
          RSP+0x?? Quad Word B
          RSP+0x?? Quad Word C
          RSP      Quad Word D

        We will now set the following in preparation for your code:
          (stack) [{hex(self.RSP_INIT)}:{hex(self.init_rsp)}] = {[hex(val) for val in self.init_mem_stack]} (list of things)
        """

    def trace(self):
        self.start()
        expected = sum(self.init_mem_stack) // 4
        yield self[self.init_rsp - 8 : self.init_rsp] == (expected).to_bytes(8, "little"), f"[{hex(self.init_rsp - 8)}] expected to be {hex(expected)}, but was {hex(int.from_bytes(self[self.init_rsp - 8 : self.init_rsp], 'little'))} instead"
        yield self.rsp == self.init_rsp - 8, f"rsp expected to be {hex(self.init_rsp - 8)}, but was {hex(self.rsp)} instead"
{% endraw %}
