{% raw %}
class ASMLevel12(ASMBase):
    """
    Read from memory
    """

    init_value = random.randint(1000000, 2000000)

    dynamic_values = True
    memory_use = True

    @property
    def init_memory(self):
        return {self.DATA_ADDR: self.init_value.to_bytes(8, "little")}

    @property
    def description(self):
        return f"""
        Up until now you have worked with registers as the only way for storing things, essentially
        variables such as 'x' in math.

        However, we can also store bytes into memory!

        Recall that memory can be addressed, and each address contains something at that location.

        Note that this is similar to addresses in real life!

        As an example: the real address '699 S Mill Ave, Tempe, AZ
        85281' maps to the 'ASU Brickyard'.

        We would also say it points to 'ASU Brickyard'.

        We can represent this like:
          ['699 S Mill Ave, Tempe, AZ 85281'] = 'ASU Brickyard'

        The address is special because it is unique.

        But that also does not mean other addresses can't point to the same thing (as someone can have multiple houses).

        Memory is exactly the same!

        For instance, the address in memory that your code is stored (when we take it from you) is {hex(self.BASE_ADDR)}.

        In x86 we can access the thing at a memory location, called dereferencing, like so:
          mov rax, [some_address]        <=>     Moves the thing at 'some_address' into rax

        This also works with things in registers:
          mov rax, [rdi]         <=>     Moves the thing stored at the address of what rdi holds to rax

        This works the same for writing to memory:
          mov [rax], rdi         <=>     Moves rdi to the address of what rax holds.

        So if rax was 0xdeadbeef, then rdi would get stored at the address 0xdeadbeef:
          [0xdeadbeef] = rdi

        Note: memory is linear, and in x86_64, it goes from 0 - 0xffffffffffffffff (yes, huge).

        Please perform the following:
          Place the value stored at 0x404000 into rax

        Make sure the value in rax is the original value stored at 0x404000.

        We will now set the following in preparation for your code:
          [0x404000] = {hex(self.init_value)}
        """

    def trace(self):
        self.start()
        yield self.rax == self.init_value, f"rax was expected to be {hex(self.init_value)}, but instead was {hex(self.rax)}"
{% endraw %}
