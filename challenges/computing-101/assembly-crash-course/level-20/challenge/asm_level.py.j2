{% raw %}
class ASMLevel27(ASMBase):
    """
    Compute average of ints array
    """

    init_rdi = ASMBase.DATA_ADDR + (random.randint(10, 100) * 8)
    init_rsi = random.randint(50, 100)
    init_mem_data = [random.randint(0, 2 ** 32 - 1) for _ in range(init_rsi)]

    interrupt_memory_read_base = init_rdi
    interrupt_memory_read_length = 10

    dynamic_values = True
    ip_control = True

    @property
    def init_memory(self):
        return {
            self.init_rdi + (8 * i): value.to_bytes(8, "little")
            for i, value in enumerate(self.init_mem_data)
        }

    @property
    def description(self):
        return f"""
        In a previous level you computed the average of 4 integer quad words, which
        was a fixed amount of things to compute, but how do you work with sizes you get when
        the program is running?

        In most programming languages a structure exists called the
        for-loop, which allows you to do a set of instructions for a bounded amount of times.
        The bounded amount can be either known before or during the programs run, during meaning
        the value is given to you dynamically.

        As an example, a for-loop can be used to compute the sum of the numbers 1 to n:
          sum = 0
          i = 1
          while i <= n:
            sum += i
            i += 1

        Please compute the average of n consecutive quad words, where:
          rdi = memory address of the 1st quad word
          rsi = n (amount to loop for)
          rax = average computed

        We will now set the following in preparation for your code:
          [{hex(self.init_rdi)}:{hex(self.init_rdi + (self.init_rsi * 8))}] = {{n qwords]}}
          rdi = {hex(self.init_rdi)}
          rsi = {self.init_rsi}
        """

    def trace(self):
        self.start()
        expected = sum(self.init_mem_data) // self.init_rsi
        yield self.rax == expected, f"rax was expected to be {hex(expected)}, but instead was {hex(self.rax)}"
{% endraw %}
