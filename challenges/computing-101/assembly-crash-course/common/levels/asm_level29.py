{% raw %}
class ASMLevel29(ASMBase):
    """
    strchr as function
    """
    foo_code = f"""
        mov rax, 0x20
        add rax, rdi
        ret
        """
    harness_code = f"""
        mov rax, {ASMBase.BASE_ADDR}
        call rax
        """
    multi_test = True
    functions = True

    def __init__(self, *args, **kwargs):
        self.foo = pwnlib.asm.asm(self.foo_code)
        self.harness = pwnlib.asm.asm(self.harness_code)
        super().__init__(*args, **kwargs)

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
        self.init_memory = {
            self.LIB_ADDR: self.foo,
            self.LIB_ADDR + 0x100: self.harness,
        }

        self.test_string = test_string

        if self.init_rdi:
            self.init_memory[self.init_rdi] = self.test_string
            self.interrupt_memory_read_base = self.init_rdi
            self.interrupt_memory_read_length = 10

    @property
    def description(self):
        return f"""
        In previous levels you implemented a while loop to count the number of
        consecutive non-zero bytes in a contiguous region of memory.

        In this level you will be provided with a contiguous region of memory again and will loop
        over each performing a conditional operation till a zero byte is reached.
        All of which will be contained in a function!

        A function is a callable segment of code that does not destroy control flow.

        Functions use the instructions "call" and "ret".

        The "call" instruction pushes the memory address of the next instruction onto
        the stack and then jumps to the value stored in the first argument.

        Let's use the following instructions as an example:
          0x1021 mov rax, 0x400000
          0x1028 call rax
          0x102a mov [rsi], rax

        1. call pushes 0x102a, the address of the next instruction, onto the stack.
        2. call jumps to 0x400000, the value stored in rax.

        The "ret" instruction is the opposite of "call".

        ret pops the top value off of the stack and jumps to it.

        Let's use the following instructions and stack as an example:

                                      Stack ADDR  VALUE
          0x103f mov rax, rdx         RSP + 0x8   0xdeadbeef
          0x1042 ret                  RSP + 0x0   0x0000102a

        Here, ret will jump to 0x102a

        Please implement the following logic:
          str_lower(src_addr):
            i = 0
            if src_addr != 0:
              while [src_addr] != 0x00:
                if [src_addr] <= 0x5a:
                  [src_addr] = foo([src_addr])
                  i += 1
                src_addr += 1
            return i

        foo is provided at {hex(self.LIB_ADDR)}.
        foo takes a single argument as a value and returns a value.

        All functions (foo and str_lower) must follow the Linux amd64 calling convention (also known as System V AMD64 ABI):
          https://en.wikipedia.org/wiki/X86_calling_conventions#System_V_AMD64_ABI

        Therefore, your function str_lower should look for src_addr in rdi and place the function return in rax.

        An important note is that src_addr is an address in memory (where the string is located) and [src_addr] refers to the byte that exists at src_addr.

        Therefore, the function foo accepts a byte as its first argument and returns a byte.

        We will now run multiple tests on your code, here is an example run:
          (data) [{hex(self.DATA_ADDR)}] = {{10 random bytes}},
          rdi = {hex(self.DATA_ADDR)}
        """

    def trace(self):
        begin_until = (self.LIB_ADDR + 0x100, self.LIB_ADDR + 0x100 + len(self.harness))
        for i in range(100):
            self.create()
            self.start(begin_until)
            yield self[self.init_rdi : self.init_rdi + len(self.test_string)] == self.test_string.lower(), f"In attempt {i+1}, [{hex(self.init_rdi)}] was not properly lower cased"
            yield self.rax == sum(chr(b).isupper() for b in self.test_string), f"In attempt {i+1}, expected rax to be {hex(sum(chr(b).isupper() for b in self.test_string))}, but was {hex(self.rax)} instead"

        self.create(init_rdi=0)
        self.start(begin_until)
        yield self.rax == 0, f"Did not handle src_addr being 0"

        self.create(test_string=b"\0")
        self.start(begin_until)
        yield self.rax == 0, f"Did not handle src_addr pointing to 0"
{% endraw %}
