{% raw %}
class ASMLevel31(ASMBase):
    harness_code = f"""
        mov rax, {ASMBase.BASE_ADDR}
        call rax
        """
    checker_code = """
        mov rsi, 0x02fcb89582a24631;
        mov rax, 0x404200;
        mov [rax], rsi;
        add rax, 0x08;
        mov rsi, 0x000081c098443b7f;
        mov [rax], rsi;

        mov rsi, 0x6568745f6b636168;
        mov rax, 0x404100;
        mov [rax], rsi;
        add rax, 0x08;
        mov rsi, 0x0000646c726f775f;
        mov [rax], rsi;

        mov rax, 0x404000;
        mov rbx, 0x404200;
        mov rsi, 0;

        loop:
        mov cl, [rax+rsi];
        mov dl, [rbx+rsi];

        test cl, cl;
        je done;
        test dl, dl;
        je done;

        add cl, dl;
        mov [rax+rsi], cl;
        inc rsi;

        jmp loop;

        done:
        mov rsi, 0;
        mov rbx, 0x404100;

        check:
        mov cl, [rax+rsi];
        mov dl, [rbx+rsi];

        cmp cl, dl
        jne fail
        test cl, cl;
        je pass;
        test dl, dl;
        je pass;

        inc rsi;
        jmp check;

        fail:
        mov rax, 0;
        jmp exit;

        pass:
        mov rax, 1;

        exit:
        ret;
        """

    def __init__(self, *args, **kwargs):
        self.harness = pwnlib.asm.asm(self.harness_code)
        self.mangler = pwnlib.asm.asm(self.checker_code)
        super().__init__(*args, **kwargs)

    def init(self):
        self.DATA_ADDR
        self.init_memory = {
            self.LIB_ADDR: self.harness,
            self.LIB_ADDR + 0x100: self.mangler,
        }

    @property
    def description(self):
        return f"""
        In the past levels, you were mostly focused on writing assembly.

        For this level, we'll focus on reading it instead!

        We will be providing you with a snippet of assembly code that will be executed after any assembly that you provide.

        This snippet will be modifying a series of bytes that ends in a null byte (hint: a string!) with the intention of garbling your input.

        Then, that series of bytes will be checked against an expected result.

        Finally, if the input you provide results in this check being passed, you'll get the flag!

        Here's the snippet of code in question:
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{checker_code}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        The goal of this challenge is conceptually simple: write assembly that populates the buffer at {self.DATA_ADDR:#08x}
        with the correct data that causes the above snippet to return with rax == 1.

        Note that this challenge will append the above assembly to your input, so it will execute directly after.

        Finally, your input is treated as part of a function (your code will be called), so make sure you restore the stack if you end up using it at all.

        Assumptions:
          The bytes for your input will start at: {self.DATA_ADDR:#08x}.
          The bytes for your input end with a null byte (0x00).
          Your input will be a valid ASCII string after it has been mangled.

        Constraints:
          You must load the correct input data at: {self.DATA_ADDR:#08x}.
          The above assembly code will be compiled and appended to your input.
        """

    def create(self, *args, **kwargs):
        self.asm += self.mangler
        super().create(*args, **kwargs)

    def trace(self):
        self.create()
        self.start((self.LIB_ADDR, self.LIB_ADDR + len(self.harness)))
        yield self.rax == 1, f"rax was expected to be 1, but was {hex(self.rax)} instead"
{% endraw %}
