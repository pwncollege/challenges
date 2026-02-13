{% raw %}
class ASMLevel28(ASMBase):
    """
    Implement strlen
    """

    multi_test = True
    ip_control = True

    def init(self, *, init_rdi=None, test_string=None):
        if init_rdi is None:
            init_rdi = self.DATA_ADDR + (random.randint(10, 100) * 8)
        if test_string is None:
            test_string = bytes(
                [
                    *random.choices(
                        string.ascii_letters.encode(), k=random.randint(1, 1000)
                    ),
                    0,
                ]
            )

        self.init_rdi = init_rdi
        self.init_memory = {}

        self.test_string = test_string

        if self.init_rdi:
            self.init_memory[self.init_rdi] = self.test_string
            self.interrupt_memory_read_base = self.init_rdi
            self.interrupt_memory_read_length = 10

    @property
    def description(self):
        return f"""
        In previous levels you discovered the for-loop to iterate for a *number* of times, both dynamically and
        statically known, but what happens when you want to iterate until you meet a condition?

        A second loop structure exists called the while-loop to fill this demand.

        In the while-loop you iterate until a condition is met.

        As an example, say we had a location in memory with adjacent numbers and we wanted
        to get the average of all the numbers until we find one bigger or equal to 0xff:
          average = 0
          i = 0
          while x[i] < 0xff:
            average += x[i]
            i += 1
          average /= i

        Using the above knowledge, please perform the following:
          Count the consecutive non-zero bytes in a contiguous region of memory, where:
            rdi = memory address of the 1st byte
            rax = number of consecutive non-zero bytes

        Additionally, if rdi = 0, then set rax = 0 (we will check)!

        An example test-case, let:
          rdi = 0x1000
          [0x1000] = 0x41
          [0x1001] = 0x42
          [0x1002] = 0x43
          [0x1003] = 0x00

        then: rax = 3 should be set

        We will now run multiple tests on your code, here is an example run:
          (data) [{hex(self.DATA_ADDR)}] = {{10 random bytes}},
          rdi = {hex(self.DATA_ADDR)}
        """

    def trace(self):
        for i in range(100):
            self.create()
            self.start()
            yield self.rax == len(self.test_string) - 1, f"In attempt {i+1}, rax was expected to be {hex(len(self.test_string) - 1)}, but was {hex(self.rax)} instead"

        self.create(init_rdi=0)
        self.start()
        yield self.rax == 0, f"Did not handle rdi = 0 case"

        self.create(test_string=b"\0")
        self.start()
        yield self.rax == 0, f"Did not handle empty string case"
{% endraw %}
