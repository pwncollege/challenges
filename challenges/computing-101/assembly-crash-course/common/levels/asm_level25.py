{% raw %}
class ASMLevel25(ASMBase):
    """
    If statements
    """

    init_rdi = ASMBase.DATA_ADDR + random.randint(0x0, 0x100)

    multi_test = True
    ip_control = True

    def init(self):
        self.selector = random.choice(
            [0x7F454C46, 0x00005A4D, random.randint(0, 2 ** 31 - 1)]
        )
        self.init_values = [random.randint(-(2 ** 16), 2 ** 16) for _ in range(3)]
        self.init_memory = {
            self.init_rdi: b"".join(
                value.to_bytes(4, "little", signed=True)
                for value in [self.selector, *self.init_values]
            )
        }

    @property
    def description(self):
        return f"""
        We will now introduce you to conditional jumps--one of the most valuable instructions in x86.
        In higher level programming languages, an if-else structure exists to do things like:
          if x is even:
            is_even = 1
          else:
           is_even = 0

        This should look familiar, since it is implementable in only bit-logic, which you've done in a prior level.

        In these structures, we can control the program's control flow based on dynamic values provided to the program.

        Implementing the above logic with jmps can be done like so:

        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ; assume rdi = x, rax is output
        ; rdx = rdi mod 2
        mov rax, rdi
        mov rsi, 2
        div rsi
        ; remainder is 0 if even
        cmp rdx, 0
        ; jump to not_even code is its not 0
        jne not_even
        ; fall through to even code
        mov rbx, 1
        jmp done
        ; jump to this only when not_even
        not_even:
        mov rbx, 0
        done:
        mov rax, rbx
        ; more instructions here
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Often though, you want more than just a single 'if-else'.

        Sometimes you want two if checks, followed by an else.

        To do this, you need to make sure that you have control flow that 'falls-through' to the next `if` after it fails.

        All must jump to the same `done` after execution to avoid the else.

        There are many jump types in x86, it will help to learn how they can be used.

        Nearly all of them rely on something called the ZF, the Zero Flag.

        The ZF is set to 1 when a cmp is equal. 0 otherwise.

        Using the above knowledge, implement the following:
          if [x] is 0x7f454c46:
            y = [x+4] + [x+8] + [x+12]
          else if [x] is 0x00005A4D:
            y = [x+4] - [x+8] - [x+12]
          else:
            y = [x+4] * [x+8] * [x+12]

        where:
          x = rdi, y = rax.

        Assume each dereferenced value is a signed dword.
        This means the values can start as a negative value at each memory position.

        A valid solution will use the following at least once:
          jmp (any variant), cmp

        We will now run multiple tests on your code, here is an example run:
          (data) [{hex(self.DATA_ADDR)}] = {{4 random dwords]}}
          rdi = {hex(self.DATA_ADDR)}
        """

    def trace(self):
        for i in range(100):
            self.create()
            self.start()
            if self.selector == 0x7F454C46:
                correct = (
                    self.init_values[0] + self.init_values[1] + self.init_values[2]
                ) & 0xFFFFFFFF
            elif self.selector == 0x00005A4D:
                correct = (
                    self.init_values[0] - self.init_values[1] - self.init_values[2]
                ) & 0xFFFFFFFF
            else:
                correct = (
                    self.init_values[0] * self.init_values[1] * self.init_values[2]
                ) & 0xFFFFFFFF
            yield self.rax == correct, f"In attempt {i+1}, rax was expected to be {hex(correct)}, but was {hex(self.rax)} instead"
{% endraw %}
