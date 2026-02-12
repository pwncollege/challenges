{% raw %}
class ASMLevel1(ASMBase):
    """
    Set register
    """

    registers_use = True

    @property
    def description(self):
        return f"""
        In this level you will work with registers! Please set the following:
          rdi = 0x1337
        """

    def trace(self):
        self.start()
        yield self.rdi == 0x1337, f"rdi was expected to be 0x1337, but was {hex(self.rdi)} instead"
{% endraw %}
