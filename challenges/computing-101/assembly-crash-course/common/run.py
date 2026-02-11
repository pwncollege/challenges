#!/usr/bin/exec-suid --real -- /bin/python3 -I

import os

os.environ["PATH"] = "/challenge/bin:/bin:/usr/bin:/usr/local/bin"
os.environ["TERM"] = "xterm-256color"

import sys
import re
import magic
import collections
import string
import random
import textwrap
import pathlib
from collections import defaultdict

import pwnlib
import pwnlib.asm
import pwnlib.elf
from unicorn import *
from unicorn.x86_const import *
from capstone import *

pwnlib.context.context.update(arch="amd64")
builtin_print = print
print = lambda text: builtin_print(re.sub("\n{2,}", "\n\n", textwrap.dedent(str(text))))

config = (pathlib.Path(__file__).parent / ".config").read_text()
level = int(config)

os.setuid(os.geteuid())


class ASMBase:
    """
    ASM:
    A set of levels to teach people the basics of x86 assembly:
    - registers_use
    - stack
    - functions
    - control statements
    Level Layout:
    === Reg ===
    1. Reg write
    2. Reg modify
    3. Reg complex use
    4. Integer Division
    5. Modulo
    6. Smaller register access
    === Bits in Registers ===
    7. Shifting bits
    8. Logic gates as a mov (bit logic)
    9. Hard bit logic challenge
    === Mem Access ===
    10. Read & Write from static memory location
    11. Sized read & write from static memory
    12. R/W to dynamic memory (stored in registers)
    13. Access adjacent memory given at runtime
    === Stack ===
    14. Pop from stack, modify, push back
    15. Stack operations as a swap
    16. r/w from stack without pop (rsp operations)
    === Control Statements ===
    17. Unconditional jumps (jump trampoline, relative and absolute)
    18. If statement jumps (computing value based on a header in mem)
    19. Switch Statements
    20. For-Loop (summing n numbers in memory)
    21. While-Loop (implementing strlen, stop on null)
    === Functions ===
    22. Making your own function, calling ours
    23. Making your own function with stack vars (the stack frame)
    """

    BASE_ADDR = 0x400000
    CODE_ADDR = BASE_ADDR
    LIB_ADDR = BASE_ADDR + 0x3000
    DATA_ADDR = BASE_ADDR + 0x4000
    BASE_STACK = 0x7FFFFF000000
    RSP_INIT = BASE_STACK + 0x200000
    REG_MAP = {
        "rax": UC_X86_REG_RAX,
        "rbx": UC_X86_REG_RBX,
        "rcx": UC_X86_REG_RCX,
        "rdx": UC_X86_REG_RDX,
        "rsi": UC_X86_REG_RSI,
        "rdi": UC_X86_REG_RDI,
        "rbp": UC_X86_REG_RBP,
        "rsp": UC_X86_REG_RSP,
        "r8": UC_X86_REG_R8,
        "r9": UC_X86_REG_R9,
        "r10": UC_X86_REG_R10,
        "r11": UC_X86_REG_R11,
        "r12": UC_X86_REG_R12,
        "r13": UC_X86_REG_R13,
        "r14": UC_X86_REG_R14,
        "r15": UC_X86_REG_R15,
        "rip": UC_X86_REG_RIP,
        "efl": UC_X86_REG_EFLAGS,
        "cs": UC_X86_REG_CS,
        "ds": UC_X86_REG_DS,
        "es": UC_X86_REG_ES,
        "fs": UC_X86_REG_FS,
        "gs": UC_X86_REG_GS,
        "ss": UC_X86_REG_SS,
    }

    init_memory = {}
    secret_key = random.randint(0, 0xFFFFFFFFFFFFFFFF)

    registers_use = False
    dynamic_values = False
    memory_use = False
    stack_use = False
    bit_logic = False
    ip_control = False
    multi_test = False
    functions = False

    whitelist = None
    blacklist = None

    interrupt_stack_read_length = 4
    interrupt_memory_read_length = 4
    interrupt_memory_read_base = DATA_ADDR

    def __init__(self, asm=None):
        self.asm = asm

        self.emu = None
        self.bb_trace = []

        self.init()

    @property
    def description(self):
        raise NotImplementedError

    @property
    def init_register_values(self):
        return {
            attr: getattr(self, attr)
            for attr in dir(self)
            if attr.startswith("init_") and attr[5:] in self.REG_MAP
        }

    def trace(self):
        raise NotImplementedError

    def init(self, *args, **kwargs):
        pass

    def create(self, *args, **kwargs):
        self.init(*args, **kwargs)

        self.emu = Uc(UC_ARCH_X86, UC_MODE_64)
        self.emu.mem_map(self.BASE_ADDR, 2 * 1024 * 1024)
        self.emu.mem_write(self.CODE_ADDR, self.asm)
        self.emu.mem_map(self.BASE_STACK, 2 * 1024 * 1024)
        self.rsp = self.RSP_INIT

        for register, value in self.init_register_values.items():
            setattr(self, register[5:], value)

        for address, value in self.init_memory.items():
            self[address] = value

        self.emu.hook_add(UC_HOOK_BLOCK, self.block_hook, begin=self.CODE_ADDR)
        self.emu.hook_add(
            UC_HOOK_INSN, self.syscall_hook, None, 1, 0, UC_X86_INS_SYSCALL
        )
        self.emu.hook_add(UC_HOOK_CODE, self.code_hook)
        self.emu.hook_add(UC_HOOK_INTR, self.intr_hook)

        if self.whitelist is not None:
            self.emu.hook_add(UC_HOOK_CODE, self.whitelist_hook)
        if self.blacklist is not None:
            self.emu.hook_add(UC_HOOK_CODE, self.blacklist_hook)

    def start(self, begin_until=None):
        if begin_until is None:
            begin_until = (self.CODE_ADDR, self.CODE_ADDR + len(self.asm))
        begin, until = begin_until
        self.emu.emu_start(begin, until)

    def run(self):
        hints = ""

        if self.registers_use:
            hints += """
            In this level you will be working with registers. You will be asked to modify
            or read from registers.
            """

        if self.dynamic_values:
            hints += """
            We will now set some values in memory dynamically before each run. On each run
            the values will change. This means you will need to do some type of formulaic
            operation with registers. We will tell you which registers are set beforehand
            and where you should put the result. In most cases, its rax.
            """

        if self.memory_use:
            hints += """
            In this level you will be working with memory. This will require you to read or write
            to things stored linearly in memory. If you are confused, go look at the linear
            addressing module in 'ike. You may also be asked to dereference things, possibly multiple
            times, to things we dynamically put in memory for your use.
            """

        if self.bit_logic:
            hints += """
            In this level you will be working with bit logic and operations. This will involve heavy use of
            directly interacting with bits stored in a register or memory location. You will also likely
            need to make use of the logic instructions in x86: and, or, not, xor.
            """

        if self.stack_use:
            hints += """
            In this level you will be working with the stack, the memory region that dynamically expands
            and shrinks. You will be required to read and write to the stack, which may require you to use
            the pop and push instructions. You may also need to use the stack pointer register (rsp) to know
            where the stack is pointing.
            """

        if self.ip_control:
            hints += """
            In this level you will be working with control flow manipulation. This involves using instructions
            to both indirectly and directly control the special register `rip`, the instruction pointer.
            You will use instructions such as: jmp, call, cmp, and their alternatives to implement the requested behavior.
            """

        if self.multi_test:
            hints += """
            We will be testing your code multiple times in this level with dynamic values! This means we will
            be running your code in a variety of random ways to verify that the logic is robust enough to
            survive normal use.
            """

        if self.functions:
            hints += """
            In this level you will be working with functions! This will involve manipulating the instruction pointer (rip),
            as well as doing harder tasks than normal. You may be asked to use the stack to store values
            or call functions that we provide you.
            """

        print(hints)
        print(self.description)

        if len(sys.argv) > 1:
            m = magic.from_file(sys.argv[1])
            if m.startswith("ELF"):
                print("Extracting binary code from provided ELF file...")
                self.asm = pwnlib.elf.ELF(sys.argv[1]).get_section_by_name(".text").data()
            else:
                print(f"Unsupported file type ({m}) for argument {sys.argv[1]}.")

        if not self.asm:
            print(f"You ran me without an argument. You can re-run with `{sys.argv[0]} /path/to/your/elf` to input an ELF file, or just give me your assembled and extracted code in bytes (up to 0x1000 bytes): ")
            self.asm = sys.stdin.buffer.read1(0x1000)

            # assuming no hex-only assembly challenges
            if all((c in (string.hexdigits+string.whitespace).encode()) for c in self.asm):
                print("")
                print("ERROR: It looks like your input is hex-ecoded! Please provide")
                print("the actual unencoded bytes!")
                sys.exit(1)

            if all((c in string.printable.encode()) for c in self.asm):
                print("")
                print("WARNING: It looks like your input might not be assembled binary")
                print("code, but assembly source code. This challenge needs the")
                print("raw binary assembled code as input.")
                print("")

        self.create()

        print("Executing your code...")
        print("---------------- CODE ----------------")
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        for i in md.disasm(self.asm, self.CODE_ADDR):
            print("0x%x:\t%-6s\t%s" % (i.address, i.mnemonic, i.op_str))
        print("--------------------------------------")

        try:
            won = True
            for condition, error in self.trace():
                if not condition:
                    print(f"Failed in the following way: {error}")
                    won = False
                    break
        except UcError as e:
            print(f"\nYour program has crashed!\n{e}\nThis was the state of your program on crash:")
            self.dump_state(self.emu)
            won = False
        except Exception as e:
            print(f"\nERROR: {e}")
            self.dump_state(self.emu)
            won = False

        if won:
            print(open("/flag").read())
        return won

    def __getattr__(self, name):
        if name in self.REG_MAP:
            return self.emu.reg_read(self.REG_MAP[name])
        if name in self.init_register_values:
            return self.init_register_values[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in self.REG_MAP:
            return self.emu.reg_write(self.REG_MAP[name], value)
        return super().__setattr__(name, value)

    def __getitem__(self, key):
        return self.emu.mem_read(key.start, key.stop - key.start)

    def __setitem__(self, key, value):
        self.emu.mem_write(key, value)

    def dump_state(self, uc):
        print(
            f"+--------------------------------------------------------------------------------+"
        )
        print(f"| {'Registers':78} |")
        print(
            f"+-------+----------------------+-------+----------------------+------------------+"
        )

        lines = []
        lc = False
        line = ""
        for reg, const in self.REG_MAP.items():
            if not lc:
                line = "| "
            # skip flag registers
            if not reg.startswith("r"):
                continue

            line += f" {reg.lower():3}  |  0x{getattr(self, reg):016x}  |"

            if not lc:
                line += " "
                lc = True
            else:
                print(f"{line:80} |")
                line = ""
                lc = False

        if line:
            print(f"{line:38} | {' ':20} | {' ':16} |")

        stack_read_amount = self.interrupt_stack_read_length
        memory_read_amount = self.interrupt_memory_read_length

        memory_read_base = self.interrupt_memory_read_base
        multiple_memory_read = False

        if isinstance(memory_read_base, list):
            multiple_memory_read = True

        read_size = 8
        # stack
        print(
            f"+---------------------------------+-------------------------+--------------------+"
        )
        print(f"| {'Stack location':31} | {'Data (bytes)':23} | {'Data (LE int)':18} |")
        print(
            f"+---------------------------------+-------------------------+--------------------+"
        )
        c = 0
        while True:
            read_addr = self.rsp + c * read_size
            if c > stack_read_amount + 10:
                break
            try:
                if (
                    f"{self[read_addr:read_addr + read_size].hex()[::-1]:0>16}"
                    == "0000000000000000"
                    and c > stack_read_amount
                ):
                    break
                print(
                    f"| 0x{read_addr:016x} (rsp+0x{(c * read_size):04x}) | {self[read_addr:read_addr+1].hex()} {self[read_addr+1:read_addr+2].hex()} {self[read_addr+2:read_addr+3].hex()} {self[read_addr+3:read_addr+4].hex()} {self[read_addr+4:read_addr+5].hex()} {self[read_addr+5:read_addr+6].hex()} {self[read_addr+6:read_addr+7].hex()} {self[read_addr+7:read_addr+8].hex()} | 0x{self[read_addr:read_addr + read_size][::-1].hex():0>16} |"
                )
            except:
                break

            c += 1

        print(
            f"+---------------------------------+-------------------------+--------------------+"
        )
        print(
            f"| {'Memory location':31} | {'Data (bytes)':23} | {'Data (LE int)':18} |"
        )
        print(
            f"+---------------------------------+-------------------------+--------------------+"
        )
        if multiple_memory_read:
            for baseaddr in memory_read_base:
                for i in range(memory_read_amount):
                    read_addr = baseaddr + i * read_size
                    print(
                        f"| {' ':2} 0x{read_addr:016x} (+0x{(i * read_size):04x}) | {self[read_addr:read_addr+1].hex()} {self[read_addr+1:read_addr+2].hex()} {self[read_addr+2:read_addr+3].hex()} {self[read_addr+3:read_addr+4].hex()} {self[read_addr+4:read_addr+5].hex()} {self[read_addr+5:read_addr+6].hex()} {self[read_addr+6:read_addr+7].hex()} {self[read_addr+7:read_addr+8].hex()} | 0x{self[read_addr:read_addr + read_size][::-1].hex():0>16} |"
                    )
                if baseaddr != memory_read_base[-1]:
                    print(
                        "|    -------------------------    |    -----------------    |    ------------    |"
                    )
        else:
            for i in range(memory_read_amount):
                read_addr = memory_read_base + i * read_size
                print(
                    f"| {' ':2} 0x{read_addr:016x} (+0x{(i * read_size):04x}) | {self[read_addr:read_addr+1].hex()} {self[read_addr+1:read_addr+2].hex()} {self[read_addr+2:read_addr+3].hex()} {self[read_addr+3:read_addr+4].hex()} {self[read_addr+4:read_addr+5].hex()} {self[read_addr+5:read_addr+6].hex()} {self[read_addr+6:read_addr+7].hex()} {self[read_addr+7:read_addr+8].hex()} | 0x{self[read_addr:read_addr + read_size][::-1].hex():0>16} |"
                )

        print(
            f"+---------------------------------+-------------------------+--------------------+"
        )

    def block_hook(self, uc, address, size, user_data):
        self.bb_trace.append(address)

    def intr_hook(self, uc, intr_num, user_data):
        if intr_num == 3:
            self.dump_state(uc)

    def syscall_hook(self, uc, user_data):
        if self.rax == 0x3C:
            uc.emu_stop()
        else:
            uc.emu_stop()
            raise Exception(f"syscall {self.rax} not supported")

    def code_hook(self, uc, address, size, user_data):
        pass

    def blacklist_hook(self, uc, address, size, user_data):
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        i = next(md.disasm(uc.mem_read(address, size), address))

        if i.mnemonic in self.blacklist:
            uc.emu_stop()
            raise Exception(f"fail: this instruction is not allowed: {i.mnemonic}")

    def whitelist_hook(self, uc, address, size, user_data):
        whitelist = self.whitelist + ["int3"]
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        i = next(md.disasm(uc.mem_read(address, size), address))

        if i.mnemonic not in whitelist:
            uc.emu_stop()
            raise Exception(f"fail: this instruction is not allowed: {i.mnemonic}")

    def get_size_of_insn_at(self, idx):
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        for i, insn in enumerate(md.disasm(self.asm, self.CODE_ADDR)):
            if i == idx:
                return insn.size


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

class ASMLevel2(ASMBase):
    """
    Set multiple registers.
    """

    registers_use = True

    @property
    def description(self):
        return f"""
        In this level you will work with multiple registers. Please set the following:
          rax = 0x1337
          r12 = 0xCAFED00D1337BEEF
          rsp = 0x31337
        """

    def trace(self):
        self.start()
        yield self.rax == 0x1337, f"rax was expected to be 0x1337, but was {hex(self.rax)} instead"
        yield self.r12 == 0xCAFED00D1337BEEF, f"r12 was expected to be 0xCAFED00D1337BEEF, but was {hex(self.r12)} instead"
        yield self.rsp == 0x31337, f"rsp was expected to be 0x10, but was {hex(self.rsp)} instead"


class ASMLevel3(ASMBase):
    """
    Modify registers
    """

    init_rdi = random.randint(0, 0x1000)

    registers_use = True
    dynamic_values = True

    @property
    def description(self):
        return f"""
        Many instructions exist in x86 that allow you to do all the normal
        math operations on registers and memory.

        For shorthand, when we say A += B, it really means A = A + B.

        Here are some useful instructions:
          add reg1, reg2       <=>     reg1 += reg2
          sub reg1, reg2       <=>     reg1 -= reg2
          imul reg1, reg2      <=>     reg1 *= reg2

        div is more complicated and we will discuss it later.
        Note: all 'regX' can be replaced by a constant or memory location

        Do the following:
          add 0x331337 to rdi

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
        """

    def trace(self):
        self.start()
        expected = self.init_rdi + 0x331337
        yield self.rdi == expected, f"rdi was expected to be {hex(expected)}, but instead was {hex(self.rdi)}"


class ASMLevel4(ASMBase):
    """
    Reg complex use: calculate y = mx + b
    """

    init_rdi = random.randint(0, 10000)
    init_rsi = random.randint(0, 10000)
    init_rdx = random.randint(0, 10000)

    registers_use = True
    dynamic_values = True

    @property
    def description(self):
        return f"""
        Using your new knowledge, please compute the following:
          f(x) = mx + b, where:
            m = rdi
            x = rsi
            b = rdx

        Place the result into rax.

        Note: there is an important difference between mul (unsigned
        multiply) and imul (signed multiply) in terms of which
        registers are used. Look at the documentation on these
        instructions to see the difference.

        In this case, you will want to use imul.

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
          rsi = {hex(self.init_rsi)}
          rdx = {hex(self.init_rdx)}
        """

    def trace(self):
        self.start()
        expected = (self.init_rdi * self.init_rsi) + self.init_rdx
        yield self.rax == expected, f"rax was expected to be {hex(expected)}, but instead was {hex(self.rax)}"


class ASMLevel5(ASMBase):
    """
    Integer Division
    """

    init_rdi = random.randint(1000, 10000)
    init_rsi = random.randint(10, 100)

    registers_use = True
    dynamic_values = True

    @property
    def description(self):
        return f"""
        Division in x86 is more special than in normal math. Math in here is
        called integer math. This means every value is a whole number.

        As an example: 10 / 3 = 3 in integer math.

        Why?

        Because 3.33 is rounded down to an integer.

        The relevant instructions for this level are:
          mov rax, reg1; div reg2

        Note: div is a special instruction that can divide
        a 128-bit dividend by a 64-bit divisor, while
        storing both the quotient and the remainder, using only one register as an operand.

        How does this complex div instruction work and operate on a
        128-bit dividend (which is twice as large as a register)?

        For the instruction: div reg, the following happens:
          rax = rdx:rax / reg
          rdx = remainder

        rdx:rax means that rdx will be the upper 64-bits of
        the 128-bit dividend and rax will be the lower 64-bits of the
        128-bit dividend.

        You must be careful about what is in rdx and rax before you call div.

        Please compute the following:
          speed = distance / time, where:
            distance = rdi
            time = rsi
            speed = rax

        Note that distance will be at most a 64-bit value, so rdx should be 0 when dividing.

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
          rsi = {hex(self.init_rsi)}
        """

    def trace(self):
        self.start()
        expected = self.init_rdi // self.init_rsi
        yield self.rax == expected, f"rax was expected to be {hex(expected)}, but instead was {hex(self.rax)}"


class ASMLevel6(ASMBase):
    """
    Modulo
    """

    init_rax = 0xFFFFFFFFFFFFFFFF
    init_rdi = random.randint(1000000, 1000000000)
    init_rsi = 2 ** random.randint(2, 16) - 1

    registers_use = True
    dynamic_values = True

    @property
    def description(self):
        return f"""
        Modulo in assembly is another interesting concept!

        x86 allows you to get the remainder after a div operation.

        For instance: 10 / 3 -> remainder = 1

        The remainder is the same as modulo, which is also called the "mod" operator.

        In most programming languages we refer to mod with the symbol '%'.

        Please compute the following:
          rdi % rsi

        Place the value in rax.

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
          rsi = {hex(self.init_rsi)}
        """

    def trace(self):
        self.start()
        expected = self.init_rdi % self.init_rsi
        yield self.rax == expected, f"rax was expected to be {hex(expected)}, but instead was {hex(self.rax)}"


class ASMLevel7(ASMBase):
    """
    Small Register Access
    """

    # Make sure that ah part is always 0 no matter the random
    init_rax = random.randint(0xCAFED00D1337BEEF, 0xFAFED00D1337BEEF) & 0xFFFFFFFFFFFF00FF

    registers_use = True
    dynamic_values = True
    whitelist = ["mov"]

    def init(self):
        self.instruction_counts = defaultdict(int)

    @property
    def description(self):
        return f"""
        Another cool concept in x86 is the ability to independently access to lower register bytes.

        Each register in x86_64 is 64 bits in size, and in the previous levels we have accessed
        the full register using rax, rdi or rsi.

        We can also access the lower bytes of each register using different register names.

        For example the lower 32 bits of rax can be accessed using eax, the lower 16 bits using ax,
        the lower 8 bits using al.

        MSB                                    LSB
        +----------------------------------------+
        |                   rax                  |
        +--------------------+-------------------+
                             |        eax        |
                             +---------+---------+
                                       |   ax    |
                                       +----+----+
                                       | ah | al |
                                       +----+----+

        Lower register bytes access is applicable to almost all registers.

        Using only one move instruction, please set the upper 8 bits of the ax register to 0x42.

        We will now set the following in preparation for your code:
          rax = {hex(self.init_rax)}
        """

    def code_hook(self, uc, address, size, user_data):
        super().code_hook(uc, address, size, user_data)
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        instruction = next(md.disasm(uc.mem_read(address, size), address))
        self.instruction_counts[instruction.mnemonic] += 1

    def trace(self):
        self.start()
        mov_count = self.instruction_counts["mov"]
        yield mov_count == 1, f"Can only use 1 mov, instead used {mov_count}"

        expected_rax = self.init_rax ^ 0x4200
        yield (expected_rax) == self.rax, f"ah was expected to be {hex(0x42)}, but instead was {hex(self.rax>>8 & 0xFF)}"


class ASMLevel8(ASMBase):
    """
    Small Register Access and mod
    """

    init_rdi = random.randint(0x0101, 0xFFFF)
    init_rsi = random.randint(0x01000001, 0xFFFFFFFF)

    registers_use = True
    dynamic_values = True
    whitelist = ["mov"]

    @property
    def description(self):
        return f"""
        It turns out that using the div operator to compute the modulo operation is slow!

        We can use a math trick to optimize the modulo operator (%). Compilers use this trick a lot.

        If we have "x % y", and y is a power of 2, such as 2^n, the result will be the lower n bits of x.

        Therefore, we can use the lower register byte access to efficiently implement modulo!

        Using only the following instruction(s):
          mov

        Please compute the following:
          rax = rdi % 256
          rbx = rsi % 65536

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
          rsi = {hex(self.init_rsi)}
        """

    def trace(self):
        self.start()
        yield (self.init_rdi % 256) == self.rax, f"rax was expected to be {hex(self.init_rdi % 256)}, but instead was {hex(self.rax)}"
        yield(self.init_rsi % 65536) == self.rbx, f"rbx was expected to be {hex(self.init_rsi % 65536)}, but instead was {hex(self.rbx)}"


class ASMLevel9(ASMBase):
    """
    Shift
    """

    init_rdi = random.randint(0x55AA55AA55AA55AA, 0x99BB99BB99BB99BB)

    dynamic_values = True
    registers_use = True
    bit_logic = True
    whitelist = ["mov", "shr", "shl"]

    @property
    def description(self):
        return f"""
        Shifting bits around in assembly is another interesting concept!

        x86 allows you to 'shift' bits around in a register.

        Take, for instance, al, the lowest 8 bits of rax.

        The value in al (in bits) is:
          rax = 10001010

        If we shift once to the left using the shl instruction:
          shl al, 1

        The new value is:
          al = 00010100

        Everything shifted to the left and the highest bit fell off
        while a new 0 was added to the right side.

        You can use this to do special things to the bits you care about.

        Shifting has the nice side affect of doing quick multiplication (by 2)
        or division (by 2), and can also be used to compute modulo.

        Here are the important instructions:
          shl reg1, reg2       <=>     Shift reg1 left by the amount in reg2
          shr reg1, reg2       <=>     Shift reg1 right by the amount in reg2
          Note: 'reg2' can be replaced by a constant or memory location

        Using only the following instructions:
          mov, shr, shl

        Please perform the following:
          Set rax to the 5th least significant byte of rdi.

        For example:
          rdi = | B7 | B6 | B5 | B4 | B3 | B2 | B1 | B0 |
          Set rax to the value of B4

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
        """

    def trace(self):
        self.start()
        expected = (self.init_rdi >> 32) & 0xFF
        yield self.rax == expected, f"rax was expected to be {hex(expected)}, but instead was {hex(self.rax)}"


class ASMLevel10(ASMBase):
    """
    Logic gates as a mov (bit logic)
    """

    init_rax = 0xFFFFFFFFFFFFFFFF
    init_rdi = random.randint(0x55AA55AA55AA55AA, 0x99BB99BB99BB99BB)
    init_rsi = random.randint(0x55AA55AA55AA55AA, 0x99BB99BB99BB99BB)

    dynamic_values = True
    registers_use = True
    bit_logic = True
    blacklist = ["mov", "xchg"]

    @property
    def description(self):
        return f"""
        Bitwise logic in assembly is yet another interesting concept!
        x86 allows you to perform logic operations bit by bit on registers.

        For the sake of this example say registers only store 8 bits.

        The values in rax and rbx are:
          rax = 10101010
          rbx = 00110011

        If we were to perform a bitwise AND of rax and rbx using the
        "and rax, rbx" instruction, the result would be calculated by
        ANDing each bit pair 1 by 1 hence why it's called a bitwise
        logic.

        So from left to right:
          1 AND 0 = 0
          0 AND 0 = 0
          1 AND 1 = 1
          0 AND 1 = 0
          ...

        Finally we combine the results together to get:
          rax = 00100010

        Here are some truth tables for reference:
              AND          OR           XOR
           A | B | X    A | B | X    A | B | X
          ---+---+---  ---+---+---  ---+---+---
           0 | 0 | 0    0 | 0 | 0    0 | 0 | 0
           0 | 1 | 0    0 | 1 | 1    0 | 1 | 1
           1 | 0 | 0    1 | 0 | 1    1 | 0 | 1
           1 | 1 | 1    1 | 1 | 1    1 | 1 | 0

        Without using the following instructions:
          mov, xchg

        Please perform the following:
          rax = rdi AND rsi

        i.e. Set rax to the value of (rdi AND rsi)

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
          rsi = {hex(self.init_rsi)}
        """

    def trace(self):
        self.start()
        expected = self.init_rdi & self.init_rsi
        yield self.rax == expected, f"rax was expected to be {hex(expected)}, but instead was {hex(self.rax)}"


class ASMLevel11(ASMBase):
    """
    Hard Bit-Logic Level
    """

    init_rax = 0xFFFFFFFFFFFFFFFF
    init_rdi = random.randint(1000000, 1000000000)

    dynamic_values = True
    registers_use = True
    bit_logic = True
    whitelist = ["and", "xor", "or"]

    @property
    def description(self):
        return f"""
        Using only the following instructions:
          and, or, xor

        Implement the following logic:
          if x is even then
            y = 1
          else
            y = 0

        where:
          x = rdi
          y = rax

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
        """

    def trace(self):
        for i in range(100):
            self.create()
            self.start()
            expected = (self.init_rdi & 0x1) ^ 0x1
            yield self.rax == expected, f"rax was expected to be {hex(expected)}, but instead was {hex(self.rax)}"

    def create(self, *args, **kwargs):
        self.init_rdi = random.randint(1000000, 1000000000)
        super().create(*args, **kwargs)



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


class ASMLevel13(ASMBase):
    """
    Write to memory
    """

    init_rax = random.randint(1000000, 2000000)

    dynamic_values = True
    memory_use = True

    @property
    def description(self):
        return f"""
        Please perform the following:
          Place the value stored in rax to 0x404000

        We will now set the following in preparation for your code:
          rax = {hex(self.init_rax)}
        """

    def trace(self):
        self.start()
        yield self[self.DATA_ADDR : self.DATA_ADDR + 8] == (self.init_rax).to_bytes(8, "little"), f"[{hex(self.DATA_ADDR)}] expected to be {hex(self.init_rax)}, instead has {hex(int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 8], 'little'))}"


class ASMLevel14(ASMBase):
    """
    Read and Write to memory
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
        Please perform the following:
          Place the value stored at 0x404000 into rax
          Increment the value stored at the address 0x404000 by 0x1337

        Make sure the value in rax is the original value stored at 0x404000 and make sure
        that [0x404000] now has the incremented value.

        We will now set the following in preparation for your code:
          [0x404000] = {hex(self.init_value)}
        """

    def trace(self):
        self.start()
        yield self.rax == self.init_value, f"rax was expected to be {hex(self.init_value)}, but instead was {hex(self.rax)}"
        yield self[self.DATA_ADDR : self.DATA_ADDR + 8] == (self.init_value + 0x1337).to_bytes(8, "little"), f"[{hex(self.DATA_ADDR)}] expected to be {hex(self.init_value + 0x1337)}, instead has {hex(int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 8], 'little'))}"


class ASMLevel15(ASMBase):
    """
    Reading just one byte from memory address
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
        Recall that registers in x86_64 are 64 bits wide, meaning they can store 64 bits.

        Similarly, each memory location can be treated as a 64 bit value.

        We refer to something that is 64 bits (8 bytes) as a quad word.

        Here is the breakdown of the names of memory sizes:
          Quad Word   = 8 Bytes = 64 bits
          Double Word = 4 bytes = 32 bits
          Word        = 2 bytes = 16 bits
          Byte        = 1 byte  = 8 bits

        In x86_64, you can access each of these sizes when dereferencing an address, just like using
        bigger or smaller register accesses:
          mov al, [address]        <=>        moves the least significant byte from address to rax
          mov ax, [address]        <=>        moves the least significant word from address to rax
          mov eax, [address]       <=>        moves the least significant double word from address to rax
          mov rax, [address]       <=>        moves the full quad word from address to rax

        Remember that moving into al does not fully clear the upper bytes.

        Please perform the following:
          Set rax to the byte at 0x404000

        We will now set the following in preparation for your code:
          [0x404000] = {hex(self.init_value)}
        """

    def trace(self):
        self.start()
        expected_value = self.init_value & 0xff
        yield self.rax == expected_value, f"rax expected to be {hex(expected_value)}, however was {hex(self.rax)}"


class ASMLevel16(ASMBase):
    """
    Reading specific sizes from addresses
    """

    init_value = random.randint(0x8000000000000000, 0x8FFFFFFFFFFFFFFF)

    dynamic_values = True
    memory_use = True

    @property
    def init_memory(self):
        return {self.DATA_ADDR: self.init_value.to_bytes(8, "little")}

    @property
    def description(self):
        return f"""
        Recall the following:
          The breakdown of the names of memory sizes:
            Quad Word   = 8 Bytes = 64 bits
            Double Word = 4 bytes = 32 bits
            Word        = 2 bytes = 16 bits
            Byte        = 1 byte  = 8 bits

        In x86_64, you can access each of these sizes when dereferencing an address, just like using
        bigger or smaller register accesses:
          mov al, [address]        <=>        moves the least significant byte from address to rax
          mov ax, [address]        <=>        moves the least significant word from address to rax
          mov eax, [address]       <=>        moves the least significant double word from address to rax
          mov rax, [address]       <=>        moves the full quad word from address to rax

        Please perform the following:
          Set rax to the byte at 0x404000
          Set rbx to the word at 0x404000
          Set rcx to the double word at 0x404000
          Set rdx to the quad word at 0x404000

        We will now set the following in preparation for your code:
          [0x404000] = {hex(self.init_value)}
        """

    def trace(self):
        self.start()
        yield self.rax == int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 1], "little"), f"rax expected to be {hex(int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 1], 'little'))}, however was {hex(self.rax)}"
        yield self.rbx == int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 2], "little"), f"rbx expected to be {hex(int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 2], 'little'))}, however was {hex(self.rbx)}"
        yield self.rcx == int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 4], "little"), f"rcx expected to be {hex(int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 4], 'little'))}, however was {hex(self.rcx)}"
        yield self.rdx == int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 8], "little"), f"rdx expected to be {hex(int.from_bytes(self[self.DATA_ADDR : self.DATA_ADDR + 8], 'little'))}, however was {hex(self.rdx)}"


class ASMLevel17(ASMBase):
    """
    Write static values to dynamic memory (of different size)
    """

    init_rdi = ASMBase.DATA_ADDR + (8 * random.randint(0, 250))
    init_rsi = ASMBase.DATA_ADDR + (8 * random.randint(250, 500))

    target_mem_rdi = 0xDEADBEEF00001337
    target_mem_rsi = 0x000000C0FFEE0000

    interrupt_memory_read_base = [init_rdi, init_rsi]

    dynamic_values = True
    memory_use = True

    @property
    def init_memory(self):
        return {self.init_rdi: b"\xff" * 8, self.init_rsi: b"\xff" * 8}

    @property
    def description(self):
        return f"""
        It is worth noting, as you may have noticed, that values are stored in reverse order of how we
        represent them.

        As an example, say:
          [0x1330] = 0x00000000deadc0de

        If you examined how it actually looked in memory, you would see:
          [0x1330] = 0xde
          [0x1331] = 0xc0
          [0x1332] = 0xad
          [0x1333] = 0xde
          [0x1334] = 0x00
          [0x1335] = 0x00
          [0x1336] = 0x00
          [0x1337] = 0x00

        This format of storing things in 'reverse' is intentional in x86, and its called "Little Endian".

        For this challenge we will give you two addresses created dynamically each run.

        The first address will be placed in rdi.
        The second will be placed in rsi.

        Using the earlier mentioned info, perform the following:
          Set [rdi] = {hex(self.target_mem_rdi)}
          Set [rsi] = {hex(self.target_mem_rsi)}

        Hint: it may require some tricks to assign a big constant to a dereferenced register.
        Try setting a register to the constant value then assigning that register to the dereferenced register.

        We will now set the following in preparation for your code:
          [{hex(self.init_rdi)}] = 0xffffffffffffffff
          [{hex(self.init_rsi)}] = 0xffffffffffffffff
          rdi = {hex(self.init_rdi)}
          rsi = {hex(self.init_rsi)}
        """

    def trace(self):
        self.start()
        yield self[self.init_rdi : self.init_rdi + 8] == self.target_mem_rdi.to_bytes(8, "little"), f"[{hex(self.init_rdi)}] expected to be {hex(self.target_mem_rdi)}, instead was {hex(int.from_bytes(self[self.init_rdi : self.init_rdi + 8], 'little'))}"
        yield self[self.init_rsi : self.init_rsi + 8] == self.target_mem_rsi.to_bytes(8, "little"), f"[{hex(self.init_rsi)}] expected to be {hex(self.target_mem_rsi)}, instead was {hex(int.from_bytes(self[self.init_rsi : self.init_rsi + 8], 'little'))}"


class ASMLevel18(ASMBase):
    """
    Write to dynamic address, consecutive
    """

    init_rdi = ASMBase.DATA_ADDR + (8 * random.randint(50, 100))
    init_rsi = ASMBase.DATA_ADDR + (8 * random.randint(200, 250))

    init_mem_rdi = random.randint(1000, 1000000)
    init_mem_rdi_next = random.randint(1000, 1000000)

    interrupt_memory_read_base = [init_rdi, init_rsi]

    dynamic_values = True
    memory_use = True

    @property
    def init_memory(self):
        return {
            self.init_rdi: self.init_mem_rdi.to_bytes(8, "little"),
            self.init_rdi + 8: self.init_mem_rdi_next.to_bytes(8, "little"),
        }

    @property
    def description(self):
        return f"""
        Recall that memory is stored linearly.

        What does that mean?

        Say we access the quad word at 0x1337:
          [0x1337] = 0x00000000deadbeef

        The real way memory is laid out is byte by byte, little endian:
          [0x1337] = 0xef
          [0x1337 + 1] = 0xbe
          [0x1337 + 2] = 0xad
          ...
          [0x1337 + 7] = 0x00

        What does this do for us?

        Well, it means that we can access things next to each other using offsets,
        similar to what was shown above.

        Say you want the 5th *byte* from an address, you can access it like:
          mov al, [address+4]

        Remember, offsets start at 0.

        Perform the following:
          Load two consecutive quad words from the address stored in rdi
          Calculate the sum of the previous steps quad words.
          Store the sum at the address in rsi

        We will now set the following in preparation for your code:
          [{hex(self.init_rdi)}] = {hex(self.init_mem_rdi)}
          [{hex(self.init_rdi + 8)}] = {hex(self.init_mem_rdi_next)}
          rdi = {hex(self.init_rdi)}
          rsi = {hex(self.init_rsi)}
        """

    def trace(self):
        self.start()
        yield self[self.init_rsi : self.init_rsi + 8] == (self.init_mem_rdi + self.init_mem_rdi_next).to_bytes(8, "little"), f"[{hex(self.init_rsi)}] expected to be {hex(self.init_mem_rdi + self.init_mem_rdi_next)}, but was {hex(int.from_bytes(self[self.init_rsi : self.init_rsi + 8], 'little'))} instead"


class ASMLevel19(ASMBase):
    """
    Pop, Modify, Push
    """

    init_rdi = random.randint(10, 100000)
    init_rsp = ASMBase.RSP_INIT - 0x8
    init_mem_rsp = random.randint(1000000, 1000000000)

    dynamic_values = True
    stack_use = True

    def init(self):
        self.instruction_counts = defaultdict(int)

    @property
    def init_memory(self):
        return {self.init_rsp: self.init_mem_rsp.to_bytes(8, "little")}

    @property
    def description(self):
        return f"""
        In these levels we are going to introduce the stack.

        The stack is a region of memory that can store values for later.

        To store a value on the stack we use the push instruction, and to retrieve a value we use pop.

        The stack is a last in first out (LIFO) memory structure, and this means
        the last value pushed in the first value popped.

        Imagine unloading plates from the dishwasher let's say there are 1 red, 1 green, and 1 blue.
        First we place the red one in the cabinet, then the green on top of the red, then the blue.

        Our stack of plates would look like:
          Top ----> Blue
                    Green
          Bottom -> Red

        Now, if we wanted a plate to make a sandwich we would retrieve the top plate from the stack
        which would be the blue one that was last into the cabinet, ergo the first one out.

        On x86, the pop instruction will take the value from the top of the stack and put it into a register.

        Similarly, the push instruction will take the value in a register and push it onto the top of the stack.

        Using these instructions, take the top value of the stack, subtract rdi from it, then put it back.

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
          (stack) [{hex(self.init_rsp)}] = {hex(self.init_mem_rsp)}
        """

    def code_hook(self, uc, address, size, user_data):
        super().code_hook(uc, address, size, user_data)
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        instruction = next(md.disasm(uc.mem_read(address, size), address))
        self.instruction_counts[instruction.mnemonic] += 1


    def trace(self):
        self.start()
        push_count = self.instruction_counts["push"]
        pop_count = self.instruction_counts["pop"]

        yield pop_count > 0, f"Use at least one pop instruction"
        yield push_count > 0, f"Use at least one push instruction"
        yield self[self.init_rsp : self.init_rsp + 8] == (self.init_mem_rsp - self.init_rdi).to_bytes(8, "little"), f"[{hex(self.init_rsp)}] expected to be {hex(self.init_mem_rsp - self.init_rdi)}, but was {hex(int.from_bytes(self[self.init_rsp : self.init_rsp + 8], 'little'))} instead"


class ASMLevel20(ASMBase):
    """
    Swap registers_use
    """

    init_rdi = random.randint(1000000, 1000000000)
    init_rsi = random.randint(1000000, 1000000000)

    dynamic_values = True
    stack_use = True
    whitelist = ["push", "pop"]

    @property
    def description(self):
        return f"""
        In this level we are going to explore the last in first out (LIFO) property of the stack.

        Using only following instructions:
          push, pop

        Swap values in rdi and rsi.
        i.e.
        If to start rdi = 2 and rsi = 5
        Then to end rdi = 5 and rsi = 2

        We will now set the following in preparation for your code:
          rdi = {hex(self.init_rdi)}
          rsi = {hex(self.init_rsi)}
        """

    def trace(self):
        self.start()
        yield self.rsi == self.init_rdi, f"rsi expected to be {hex(self.init_rdi)}, but was {hex(self.rsi)} instead"
        yield self.rdi == self.init_rsi, f"rdi expected to be {hex(self.init_rsi)}, but was {hex(self.rdi)} instead"


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


class ASMLevel22(ASMBase):
    """
    Jump to provided code with absolute jump
    """

    CODE_ADDR = ASMBase.CODE_ADDR + random.randint(0x10, 0x100)

    init_rsp = ASMBase.RSP_INIT - 0x8
    init_mem_rsp = random.randint(0x10, 0x100)

    relative_offset = 0x51
    library_code = f"""
        mov rax, 0x3c
        syscall
        """

    dynamic_values = True
    ip_control = True

    def __init__(self, *args, **kwargs):
        self.library = pwnlib.asm.asm(self.library_code)
        super().__init__(*args, **kwargs)

    @property
    def init_memory(self):
        return {
            self.init_rsp: self.init_mem_rsp.to_bytes(8, "little"),
            self.LIB_ADDR: self.library,
        }

    @property
    def description(self):
        return f"""
        Earlier, you learned how to manipulate data in a pseudo-control way, but x86 gives us actual
        instructions to manipulate control flow directly.

        There are two major ways to manipulate control flow:
         through a jump;
         through a call.

        In this level, you will work with jumps.

        There are two types of jumps:
          Unconditional jumps
          Conditional jumps

        Unconditional jumps always trigger and are not based on the results of earlier instructions.

        As you know, memory locations can store data and instructions.

        Your code will be stored at {hex(self.CODE_ADDR)} (this will change each run).

        For all jumps, there are three types:
          Relative jumps: jump + or - the next instruction.
          Absolute jumps: jump to a specific address.
          Indirect jumps: jump to the memory address specified in a register.

        In x86, absolute jumps (jump to a specific address) are accomplished by first putting the target address in a register reg, then doing jmp reg.

        In this level we will ask you to do an absolute jump.

        Perform the following:
          Jump to the absolute address {hex(self.LIB_ADDR)}

        We will now set the following in preparation for your code:
          Loading your given code at: {hex(self.CODE_ADDR)}
        """

    def trace(self):
        self.start()
        yield self.bb_trace[0] == self.CODE_ADDR, f"Expected code to start executing at {self.CODE_ADDR}"
        yield self.bb_trace[-1] == self.LIB_ADDR, f"Expected code to jump to {hex(self.LIB_ADDR)} at the end, but was {hex(self.bb_trace[-1])} instead"


class ASMLevel23(ASMBase):
    """
    Do a:
    1. relative jump
    """

    CODE_ADDR = ASMBase.CODE_ADDR + random.randint(0x10, 0x100)

    init_rsp = ASMBase.RSP_INIT - 0x8
    init_mem_rsp = random.randint(0x10, 0x100)

    relative_offset = 0x51

    dynamic_values = True
    ip_control = True

    @property
    def init_memory(self):
        return {
            self.init_rsp: self.init_mem_rsp.to_bytes(8, "little"),
        }

    @property
    def description(self):
        return f"""
        Recall that for all jumps, there are three types:
          Relative jumps
          Absolute jumps
          Indirect jumps

        In this level we will ask you to do a relative jump.

        You will need to fill space in your code with something to make this relative jump possible.

        We suggest using the `nop` instruction. It's 1 byte long and very predictable.

        In fact, the as assembler that we're using has a handy .rept directive that you can use to
        repeat assembly instructions some number of times:
          https://ftp.gnu.org/old-gnu/Manuals/gas-2.9.1/html_chapter/as_7.html

        Useful instructions for this level:
          jmp (reg1 | addr | offset) ; nop

        Hint: for the relative jump, lookup how to use `labels` in x86.

        Using the above knowledge, perform the following:
          Make the first instruction in your code a jmp
          Make that jmp a relative jump to {hex(self.relative_offset)} bytes from the current position
          At the code location where the relative jump will redirect control flow set rax to 0x1

        We will now set the following in preparation for your code:
          Loading your given code at: {hex(self.CODE_ADDR)}
        """

    def trace(self):
        self.start()
        yield self.bb_trace[0] == self.CODE_ADDR, f"Expected code to start executing at {self.CODE_ADDR}"
        yield self.bb_trace[1] == self.CODE_ADDR + self.relative_offset + self.get_size_of_insn_at(0), f"Expected code to jump to {hex(self.CODE_ADDR + self.relative_offset + self.get_size_of_insn_at(0))}, but instead jumped to {hex(self.bb_trace[1])}"
        yield self.rax == 1, f"rax expected to be {hex(1)}, however was {hex(self.rax)}"

class ASMLevel24(ASMBase):
    """
    Jump to provided code:
    1. relative jump
    2. absolute jump
    """

    CODE_ADDR = ASMBase.CODE_ADDR + random.randint(0x10, 0x100)

    init_rsp = ASMBase.RSP_INIT - 0x8
    init_mem_rsp = random.randint(0x10, 0x100)

    relative_offset = 0x51
    library_code = f"""
        mov rsi, rdi
        mov rdi, {ASMBase.secret_key}
        mov rax, 0x3c
        syscall
        """
    dynamic_values = True
    ip_control = True

    def __init__(self, *args, **kwargs):
        self.library = pwnlib.asm.asm(self.library_code)
        super().__init__(*args, **kwargs)

    @property
    def init_memory(self):
        return {
            self.init_rsp: self.init_mem_rsp.to_bytes(8, "little"),
            self.LIB_ADDR: self.library,
        }

    @property
    def description(self):
        return f"""
        Now, we will combine the two prior levels and perform the following:
          Create a two jump trampoline:
            Make the first instruction in your code a jmp
            Make that jmp a relative jump to {hex(self.relative_offset)} bytes from its current position
            At {hex(self.relative_offset)} write the following code:
              Place the top value on the stack into register rdi
              jmp to the absolute address {hex(self.LIB_ADDR)}

        We will now set the following in preparation for your code:
          Loading your given code at: {hex(self.CODE_ADDR)}
          (stack) [{hex(self.RSP_INIT - 0x8)}] = {hex(self.init_mem_rsp)}
        """

    def trace(self):
        self.start()
        # NOTE: The bb_trace checks are cursed and should be burnt to
        # the ground and redone. The key problem is that this
        # means that the student cannot put `int 3` as the
        # first instruction of the challenge (which kinda
        # breaks it). However, it's better than the prior
        # hardcoded 3 locations (as _any_ `int 3` would break
        # it).

        yield self.bb_trace[0] == self.CODE_ADDR, f"Expected code to start executing at {self.CODE_ADDR}"
        yield self.bb_trace[1] == self.CODE_ADDR + self.relative_offset + self.get_size_of_insn_at(0), f"Expected code to jump to {hex(self.CODE_ADDR + self.relative_offset + self.get_size_of_insn_at(0))}, but instead jumped to {hex(self.bb_trace[1])}"
        yield self.bb_trace[-1] == self.LIB_ADDR, f"Expected code to jump to {hex(self.LIB_ADDR)} at the end, but was {hex(self.bb_trace[-1])} instead"
        yield self.rdi == self.secret_key, f"rdi expected to be {hex(self.secret_key)}, but was {hex(self.rdi)} instead"
        yield self.rsi == self.init_mem_rsp, f"rsi expected to be {hex(self.init_mem_rsp)}, but was {hex(self.rsi)} instead"


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


class ASMLevel26(ASMBase):
    multi_test = True
    ip_control = True
    libraries_code = [
          f"""
          mov rsi, rdi
          mov rdi, {ASMBase.secret_key + i}
          mov rax, 0x3c
          syscall
          """
          for i in range(5)
    ]

    def __init__(self, *args, **kwargs):
        self.libraries = [
          pwnlib.asm.asm(library_code)
          for library_code in self.libraries_code
        ]
        super().__init__(*args, **kwargs)

    def init(self):
        self.jump_locations = [
            random.randint(self.LIB_ADDR + (200 * i), self.LIB_ADDR + (200 * i) + 100)
            for i in range(5)
        ]

        self.init_rdi = random.randint(0, 5)
        self.init_rsi = self.DATA_ADDR + random.randint(0, 1024)

        self.init_memory = {
            self.init_rsi: b"".join(
                location.to_bytes(8, "little") for location in self.jump_locations
            ),
            **{
                location: library
                for location, library in zip(self.jump_locations, self.libraries)
            },
        }

        self.instruction_counts = defaultdict(int)

    @property
    def description(self):
        return f"""
        The last jump type is the indirect jump, which is often used for switch statements in the real world.

        Switch statements are a special case of if-statements that use only numbers to determine where the control flow will go.

        Here is an example:
          switch(number):
            0: jmp do_thing_0
            1: jmp do_thing_1
            2: jmp do_thing_2
            default: jmp do_default_thing

        The switch in this example is working on `number`, which can either be 0, 1, or 2.

        In the case that `number` is not one of those numbers, the default triggers.

        You can consider this a reduced else-if type structure.

        In x86, you are already used to using numbers, so it should be no surprise that you can make if statements based on something being an exact number.

        In addition, if you know the range of the numbers, a switch statement works very well.

        Take for instance the existence of a jump table.

        A jump table is a contiguous section of memory that holds addresses of places to jump.

        In the above example, the jump table could look like:
          [0x1337] = address of do_thing_0
          [0x1337+0x8] = address of do_thing_1
          [0x1337+0x10] = address of do_thing_2
          [0x1337+0x18] = address of do_default_thing

        Using the jump table, we can greatly reduce the amount of cmps we use.

        Now all we need to check is if `number` is greater than 2.

        If it is, always do:
          jmp [0x1337+0x18]
        Otherwise:
          jmp [jump_table_address + number * 8]

        Using the above knowledge, implement the following logic:
          if rdi is 0:
            jmp {hex(self.jump_locations[0])}
          else if rdi is 1:
            jmp {hex(self.jump_locations[1])}
          else if rdi is 2:
            jmp {hex(self.jump_locations[2])}
          else if rdi is 3:
            jmp {hex(self.jump_locations[3])}
          else:
            jmp {hex(self.jump_locations[4])}

        Please do the above with the following constraints:
          Assume rdi will NOT be negative
          Use no more than 1 cmp instruction
          Use no more than 3 jumps (of any variant)
          We will provide you with the number to 'switch' on in rdi.
          We will provide you with a jump table base address in rsi.

        Here is an example table:
          [{hex(self.init_rsi + 0)}] = {hex(self.jump_locations[0])} (addrs will change)
          [{hex(self.init_rsi + 8)}] = {hex(self.jump_locations[1])}
          [{hex(self.init_rsi + 16)}] = {hex(self.jump_locations[2])}
          [{hex(self.init_rsi + 24)}] = {hex(self.jump_locations[3])}
          [{hex(self.init_rsi + 32)}] = {hex(self.jump_locations[4])}
        """

    def code_hook(self, uc, address, size, user_data):
        super().code_hook(uc, address, size, user_data)
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        instruction = next(md.disasm(uc.mem_read(address, size), address))
        self.instruction_counts[instruction.mnemonic] += 1

    def trace(self):
        for i in range(100):
            self.create()
            self.start()
            jmps = sum(
                count
                for instruction, count in self.instruction_counts.items()
                if instruction.startswith("j")
            )
            cmps = self.instruction_counts["cmp"]
            yield jmps <= 3, f"In attempt {i+1}, used {jmps} jumps which is too many"
            yield cmps <= 1, f"In attempt {i+1}, used {cmps} cmp instructions which is too many"
            yield self.rdi == min(self.init_rdi, 4) + self.secret_key, f"In attempt {i+1}, rdi was expected to be {hex(min(self.init_rdi, 4) + self.secret_key)}, but was {hex(self.rdi)} instead"
            if (i+1) % 10 == 0:
                print(f"Completed test {i+1}")


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


def main():
    challenge = globals()[f"ASMLevel{level}"]

    try:
        challenge().run()
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
