{% raw %}
class ASMLevel30(ASMBase):
    harness_code = f"""
        mov rax, {ASMBase.BASE_ADDR}
        call rax
        """

    multi_test = True
    functions = True

    def __init__(self, *args, **kwargs):
        self.harness = pwnlib.asm.asm(self.harness_code)
        super().__init__(*args, **kwargs)

    def init(self):
        test_length = random.randint(10, 40)
        test_min_value = random.randint(1, 0xFE - test_length)
        self.test_list = [
            random.randint(0, test_length // 2) + test_min_value
            for _ in range(test_length)
        ]

        self.init_rdi = self.DATA_ADDR + random.randint(1, 100)
        self.init_rsi = len(self.test_list)

        self.init_memory = {
            self.LIB_ADDR: self.harness,
            self.RSP_INIT - 0x100: b"\0" * 0x100,
            self.init_rdi: bytes(self.test_list),
        }

        self.interrupt_stack_read_length = 20

    @property
    def description(self):
        return f"""
        In the previous level, you learned how to make your first function and how to call other functions.

        Now we will work with functions that have a function stack frame.

        A function stack frame is a set of pointers and values pushed onto the stack to save things for later use and allocate space on the stack for function variables.

        First, let's talk about the special register rbp, the Stack Base Pointer.

        The rbp register is used to tell where our stack frame first started.

        As an example, say we want to construct some list (a contiguous space of memory) that is only used in our function.

        The list is 5 elements long, and each element is a dword.

        A list of 5 elements would already take 5 registers, so instead, we can make space on the stack!

        The assembly would look like:
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ; setup the base of the stack as the current top
        mov rbp, rsp
        ; move the stack 0x14 bytes (5 * 4) down
        ; acts as an allocation
        sub rsp, 0x14
        ; assign list[2] = 1337
        mov eax, 1337
        mov [rbp-0x8], eax
        ; do more operations on the list ...
        ; restore the allocated space
        mov rsp, rbp
        ret
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Notice how rbp is always used to restore the stack to where it originally was.

        If we don't restore the stack after use, we will eventually run out.

        In addition, notice how we subtracted from rsp, because the stack grows down.

        To make the stack have more space, we subtract the space we need.

        The ret and call still works the same.

        Once, again, please make function(s) that implements the following:
        most_common_byte(src_addr, size):
          i = 0
          while i <= size-1:
            curr_byte = [src_addr + i]
            [stack_base - curr_byte * 2] += 1
            i += 1

          b = 0
          max_freq = 0
          max_freq_byte = 0
          while b <= 0xff:
            if [stack_base - b * 2] > max_freq:
              max_freq = [stack_base - b * 2]
              max_freq_byte = b
            b += 1

          return max_freq_byte

        Assumptions:
          There will never be more than 0xffff of any byte
          The size will never be longer than 0xffff
          The list will have at least one element
        Constraints:
          You must put the "counting list" on the stack
          You must restore the stack like in a normal function
          You cannot modify the data at src_addr
        """

    def trace(self):
        for i in range(100):
            self.create()
            self.start((self.LIB_ADDR, self.LIB_ADDR + len(self.harness)))
            yield self.rax & 0xFF == collections.Counter(sorted(self.test_list)).most_common(1)[0][0], f"In attempt {i+1}, al should be {hex(collections.Counter(sorted(self.test_list)).most_common(1)[0][0])} but was {hex(self.rax & 0xFF)} instead"
            yield self.rsp == self.RSP_INIT, f"In attempt {i+1}, rsp should be {hex(self.RSP_INIT)}, but was {hex(self.rsp)} instead (this means that your function is leaving the stack misaligned, and that's bad)"
{% endraw %}
