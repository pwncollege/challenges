{% raw %}
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

{% endraw %}
level = {{ level }}
{% raw %}

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

{% endraw %}
{% include "common/levels/asm_level" ~ level ~ ".py" %}
{% raw %}

def main():
    challenge = globals()[f"ASMLevel{level}"]

    try:
        challenge().run()
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()

{% endraw %}
