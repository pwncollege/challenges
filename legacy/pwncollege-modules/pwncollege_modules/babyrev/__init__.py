import tempfile
import hashlib
import pwnshop
import string
import socket
import time
import pwn
import os
import re

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge
from . import assembler


class BabyKeyBase(Challenge):
    TEMPLATE_PATH = "babyrev/babykey.c"

    win_function = True

    difficulty = None
    input_size = None
    input_fd = None
    manglers = None
    crackme = False
    bin_padding = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.STRIP = not self.walkthrough

        if self.input_size is None:
            self.input_size = self.random.randrange(self.difficulty * 5, (self.difficulty + 1) * 5)

        self.solution = "".join(self.random.choices(string.ascii_lowercase, k=self.input_size))

        mangler_args = {
            "reverse": lambda: [],
            "sort": lambda: [],
            "swap": lambda: sorted(self.random.sample(range(self.input_size), k=2)),
            "xor": lambda: [
                [
                    self.random.randrange(1, 255)
                    for _ in range(self.random.randrange(1, self.difficulty + 1))
                ]
            ],
            "md5": lambda: [],
        }

        all_manglers = ["reverse", "sort", "swap", "xor"]
        if self.manglers is None:
            self.manglers = []
            for _ in range(self.difficulty):
                mangler = self.random.choice(all_manglers)
                self.manglers.append(mangler)
                if mangler == "sort":
                    all_manglers.remove(mangler)

        self.manglers = [(mangler, mangler_args[mangler]()) for mangler in self.manglers]

        self.expected_result = self.solve_manglers(self.solution, self.manglers)

        if self.bin_padding is None:
            self.bin_padding = self.random.randrange(0x10, 0x1000)

    @staticmethod
    def solve_manglers(data, manglers):
        data = data.encode("latin")
        for mangler, args in manglers:
            if mangler == "reverse":
                data = data[::-1]
            elif mangler == "sort":
                data = bytes(sorted(data))
            elif mangler == "swap":
                data_array = bytearray(data)
                data_array[args[0]] = data[args[1]]
                data_array[args[1]] = data[args[0]]
                data = bytes(data_array)
            elif mangler == "xor":
                data = bytes([i ^ j for i, j in zip(data, args[0] * len(data))])
            elif mangler == "md5":
                data = hashlib.md5(data).digest()
            else:
                raise NotImplementedError()
        return data.decode("latin")

    @staticmethod
    def HEX_LIST(list_):
        return "0x" + bytes(list_).hex()

    def verify(self, **kwargs):
        """
        Checks user input against global variable EXPECTED_RESULT with a specified set of manglers.
        """
        solution = self.solution if not self.crackme else "#" * len(self.solution)

        with self.run_challenge(**kwargs) as process:
            if self.crackme:
                elf = pwn.ELF(process.executable)

                main_start = elf.symbols["main"]
                epilogue = b"\x41\x5c\x41\x5d\x41\x5e\x41\x5f\xc3"
                for ret_addr in elf.search(epilogue):
                    if ret_addr > main_start:
                        main_end = ret_addr
                        break

                disasm = elf.disasm(main_start, main_end - main_start)
                jne_addrs = [
                    int(e, 16) for e in re.findall(r"\s+([0-9a-f]+).*jne.*", disasm)
                ]
                assert jne_addrs

                page_ptr = (elf.symbols["bin_padding"] & ~0xFFF) - 0x1000
                offsets = [jne_addr - page_ptr for jne_addr in jne_addrs]
                je = 0x74
                offsets = (offsets * self.crackme_num_bytes)[
                    : self.crackme_num_bytes
                ]

                for offset in offsets:
                    process.recvuntil("Offset (hex) to change:")
                    process.sendline(hex(offset))
                    process.recvuntil("New value (hex):")
                    process.sendline(hex(je))
                    process.recvuntil("The byte has been changed")

            process.send(solution)

            assert self.flag in process.readall()


class BabyRevNoMangler(BabyKeyBase):
    """
    Reverse engineer this challenge to find the correct license key.
    """
    difficulty = 0
    input_size = 5


class BabyRevSwapMangler(BabyKeyBase):
    """
    Reverse engineer this challenge to find the correct license key, but your input will be modified somehow before being compared to the correct key.
    """
    difficulty = 1
    input_size = 5
    manglers = ["swap"]


class BabyRevReverseMangler(BabyKeyBase):
    """
    Reverse engineer this challenge to find the correct license key, but your input will be modified somehow before being compared to the correct key.
    """
    difficulty = 1
    input_size = 5
    manglers = ["reverse"]


class BabyRevSortMangler(BabyKeyBase):
    """
    Reverse engineer this challenge to find the correct license key, but your input will be modified somehow before being compared to the correct key.
    """
    difficulty = 1
    input_size = 5
    manglers = ["sort"]


class BabyRevXORMangler(BabyKeyBase):
    """
    Reverse engineer this challenge to find the correct license key, but your input will be modified somehow before being compared to the correct key.
    """
    difficulty = 1
    input_size = 5
    manglers = ["xor"]


class BabyRev3Manglers(BabyKeyBase):
    """
    Reverse engineer this challenge to find the correct license key, but your input will be modified somehow before being compared to the correct key.
    """
    difficulty = 3


class BabyRev5Manglers(BabyKeyBase):
    """
    Reverse engineer this challenge to find the correct license key, but your input will be modified somehow before being compared to the correct key.
    """
    difficulty = 5


class BabyRev7Manglers(BabyKeyBase):
    """
    Reverse engineer this challenge to find the correct license key, but your input will be modified somehow before being compared to the correct key.
    """
    difficulty = 7


class BabyRevPatch5Bytes(BabyKeyBase):
    """
    Reverse engineer this challenge to find the correct license key, but your input will be modified somehow before being compared to the correct key. This challenge allows you to patch 5 bytes in the binary.
    """
    LINK_LIBRARIES = ["crypto"]

    difficulty = 5
    crackme = True
    crackme_num_bytes = 5
    manglers = ["md5"]
    bin_padding = None  # random
    
    def verify(self, **kwargs):
        """
        Checks user input against an md5 string, allows them to patch over 5 bytes.
        """
        self.run_challenge(**kwargs)



class BabyRevPatch1Byte(BabyKeyBase):
    """
    Reverse engineer this challenge to find the correct license key, but your input will be modified somehow before being compared to the correct key. This challenge allows you to patch 1 byte in the binary.
    """
    LINK_LIBRARIES = ["crypto"]

    difficulty = 5
    crackme = True
    crackme_num_bytes = 1
    manglers = ["md5"]
    bin_padding = None  # random
    
    def verify(self, **kwargs):
        """
        Checks user input against an md5 string, allows them to patch over 1 bytes.
        """
        self.run_challenge(**kwargs)



class BabyRevPatch2BytesIntegrityCheck(BabyKeyBase):
    """
    Reverse engineer this challenge to find the correct license key, but your input will be modified somehow before being compared to the correct key. This challenge allows you to patch 2 bytes in the binary, but performs an integrity check afterwards.
    """
    LINK_LIBRARIES = ["crypto"]

    difficulty = 5
    crackme = True
    crackme_num_bytes = 2
    crackme_integrity = True
    manglers = ["md5"]
    bin_padding = None  # random
    
    def verify(self, **kwargs):
        """
        Checks user input against an md5 string, allows them to patch over 1 bytes.
        """
        self.run_challenge(**kwargs)



class BabyVMBase(Challenge):
    TEMPLATE_PATH = "babyrev/babyvm.c"

    difficulty = None
    memory_size = 256
    memory = "\0"*256
    prerandomize = True
    rerandomize = False
    interpreted = True
    interpret_forever = True
    operand_type = "unsigned char"
    word_type = "unsigned char"

    # interpreting or just obfuscation
    direct_interpret_calls = False

    # prerandomization
    inst_definition = None
    register_order = None
    operation_order = None
    syscall_order = None
    flag_order = None

    def _shift_by(self, list_name, index):
        lst = getattr(self, list_name)
        return hex(1 << lst.index(index))

    def randomize(self, operand_type="unsigned char", force_space_sys=False):
        # randomize
        assembler.INSTRUCTION_ORDER.sort()
        assembler.SYSCALL_ORDER.sort()
        assembler.ENCODING_ORDER.sort()
        assembler.REG_ORDER.sort()
        assembler.FLAG_ORDER.sort()
        self.random.shuffle(assembler.INSTRUCTION_ORDER)
        self.random.shuffle(assembler.SYSCALL_ORDER)
        self.random.shuffle(assembler.ENCODING_ORDER)
        self.random.shuffle(assembler.REG_ORDER)
        self.random.shuffle(assembler.FLAG_ORDER)

        # for toddler, we want a level where the syscall opcode is a space (for scanf)
        if force_space_sys:
            sys_index = assembler.INSTRUCTION_ORDER.index("sys")
            assembler.INSTRUCTION_ORDER[5], assembler.INSTRUCTION_ORDER[sys_index] = "sys", assembler.INSTRUCTION_ORDER[5]

        # save to the template
        self.inst_definition = f"""{{ {operand_type} {assembler.ENCODING_ORDER[0]}; {operand_type} {assembler.ENCODING_ORDER[1]}; {operand_type} {assembler.ENCODING_ORDER[2]}; }}"""
        self.register_order = assembler.REG_ORDER
        self.operation_order = assembler.INSTRUCTION_ORDER
        self.syscall_order = assembler.SYSCALL_ORDER
        self.flag_order = assembler.FLAG_ORDER

        # generate encodings for later assembling
        assembler.ENCODING.clear()
        assembler.generate_encoding()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.STRIP = not self.walkthrough

        if self.prerandomize:
            self.randomize(operand_type=self.operand_type)

class BabyVMKeygenBase(BabyVMBase):
    mangle_key = False
    manglers = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        charset = bytes(range(256))

        self.input_size = self.random.randrange(2, 5) * (self.difficulty + 1)
        self.padding_size = self.random.randrange(1, 2) * self.difficulty
        self.input_solution = bytes(self.random.choices(charset, k=self.input_size))
        self.padding = bytes(self.random.choices(charset, k=self.padding_size))
        self.key_location = self.random.randrange(0x50, 0xa0)
        self.key_differences = [ self.random.randrange(256) for _ in range(self.input_size) ] if self.manglers else [ ]

    def verify(self, **kwargs):
        """
        Yan85 Keygen, checks user input against bytes loaded by Yan85 code
        """
        answer = bytearray(self.input_solution)
        for i,kd in enumerate(self.key_differences):
            answer[i] = (answer[i] - kd if not self.mangle_key else answer[i] + kd) % 256

        with self.run_challenge(**kwargs) as process:
            process.write(bytes(answer))
            o = process.readall()
            #print(o)
            assert self.flag in o

        answer[0] ^= 0xff
        with self.run_challenge(**kwargs) as process:
            process.write(bytes(answer))
            o = process.readall()
            #print(o)
            assert self.flag not in o

class BabyRevYan85BasicCReadExpectedMemcmpSuccessExit(BabyVMKeygenBase):
    """
    We're about to dive into reverse engineering obfuscated code!
    To better prepare you for the journey ahead, this challenge is a very straightforward crackme, but using slightly different code, memory layout, and input format.
    We will progressively obfuscate this in future levels, but this level should be a freebie!
    """
    difficulty = 1
    direct_interpret_calls = True
    c_read = True
    c_expected = True
    c_memcmp = True
    c_success = True
    c_exit = True

class BabyRevYan85BasicCReadMemcmpSuccessExit(BabyVMKeygenBase):
    """
    Let's dive into reverse engineering obfuscated code!
    This challenge is using VM-based obfuscation: reverse engineer the custom emulator and architecture to understand how to get the flag!
    If you are clever, you won't need to reverse _too_ much VM code.
    """
    difficulty = 1
    direct_interpret_calls = True
    c_read = True
    c_memcmp = True
    c_success = True
    c_exit = True
    c_read = True

class BabyRevYan85BasicCMemcmpSuccessExit(BabyVMKeygenBase):
    """
    Let's dive into reverse engineering obfuscated code!
    This challenge is using VM-based obfuscation: reverse engineer the custom emulator and architecture to understand how to get the flag!
    If you are clever, you won't need to reverse _too_ much VM code.
    """
    difficulty = 1
    direct_interpret_calls = True
    c_memcmp = True
    c_success = True
    c_exit = True

class BabyRevYan85BasicMemcmp(BabyVMKeygenBase):
    """
    Let's dive into reverse engineering obfuscated code!
    This challenge is using VM-based obfuscation: reverse engineer the custom emulator and architecture to understand how to get the flag!
    If you are clever, you won't need to reverse _too_ much VM code.
    """
    difficulty = 1
    direct_interpret_calls = True
    c_memcmp = True

class BabyRevYan85ManualMemcmp(BabyVMKeygenBase):
    """
    Let's continue deeper in reverse engineering obfuscated code!
    This challenge is using VM-based obfuscation: reverse engineer the custom emulator and architecture to understand how to get the flag!
    """
    difficulty = 1
    direct_interpret_calls = True


class BabyRevYan85Manglers(BabyVMKeygenBase):
    """
    This challenge is using VM-based obfuscation: reverse engineer the custom emulator and architecture to understand how to get the flag!
    """
    difficulty = 2
    manglers = True
    direct_interpret_calls = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mangle_key = self.random.choice([True, False])

class BabyRevYan85MangledMemcmp(BabyVMKeygenBase):
    """
    This challenge is using VM-based obfuscation: reverse engineer the custom emulator and architecture to understand how to get the flag!
    """
    difficulty = 2
    manglers = True
    mangle_memcmp = True
    direct_interpret_calls = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mangle_key = self.random.choice([True, False])

class BabyVMKeygenProgramBase(BabyVMKeygenBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.program, self.memory = self.gen_asm()
        self.vm_code = ", ".join(hex(i) for i in self.program)
        self.vm_code_length = len(self.program)
        self.vm_mem = ", ".join(hex(i) for i in self.memory)

class BabyRevYan85EmulatorBasic(BabyVMKeygenProgramBase):
    """
    This challenge is using VM-based obfuscation: reverse engineer the custom emulator and architecture to understand how to get the flag!
    This is a full end-to-end obfuscated challenge, like you might see in real-world obfuscated code!
    """
    difficulty = 2

    def gen_asm(self):
        return assembler.generalized(self.padding+self.input_solution, self.key_location, padding_size=self.padding_size, r=self.random), b'\0'*256

class BabyRevYan85EmulatorMangled(BabyVMKeygenProgramBase):
    """
    Reverse engineer this custom emulator and architecture to understand how to get the flag! 
    """
    difficulty = 6
    manglers = True

    def gen_asm(self):
        memory = (
            (b'\0'*self.key_location+self.padding+self.input_solution).ljust(0x90, b'\0') +
            b"CORRECT! Here is your flag:\nINCORRECT!KEY: /flag\0"
        ).ljust(256, b'\0')
        assert len(memory) <= 256
        idx_correct = memory.index(b"CORRECT!")
        idx_incorrect = memory.index(b"INCORRECT!")
        idx_enter = memory.index(b"KEY: ")
        idx_flagpath = memory.index(b"/flag\0")
        program = assembler.generalized(
            self.padding+self.input_solution,
            self.key_location,
            padding_size=self.padding_size,
            key_differences=self.key_differences,
            store_key=False,
            idx_correct=idx_correct, len_correct=idx_incorrect - idx_correct,
            idx_incorrect=idx_incorrect, len_incorrect=idx_enter - idx_incorrect,
            idx_enter=idx_enter, len_enter=5,
            idx_flagpath=idx_flagpath,
            r=self.random
        )
        with open(f"{self.work_dir}/program", "wb") as o:
            o.write(program)
        return program, memory


class BabyRevYan85EmulatorUserInput(BabyVMBase):
    """
    Reverse engineer this custom emulator and architecture, and write your own custom shellcode to get the flag.
    """
    def verify(self, **kwargs):
        """
        Yan85 full emulator, directly interprets user input as yan85.
        """
        with self.run_challenge(**kwargs) as process:
            process.write(assembler.program_getflag())
            o = process.readall()
            assert self.flag in o
        with self.run_challenge(**kwargs) as process:
            process.write(b"nope")
            o = process.readall()
            assert self.flag not in o

class BabyRevYan85BlindEmulatorUserInput(BabyVMBase):
    """
    Reverse engineer this custom emulator and architecture, and write your own custom shellcode to get the flag, with a twist.
    This is the final boss.
    Are you a true Yan-head?
    """
    prerandomize = False
    rerandomize = True
    seed_flag = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = [ "unsigned char op;", "unsigned char arg1;", "unsigned char arg2;" ]
        self.random.shuffle(layout)
        self.instruction_layout = " ".join(layout)

    def arrange_inst(self, op, arg1, arg2):
        ss = self.instruction_layout
        ss = ss.replace("unsigned char op;", str(op))
        ss = ss.replace("unsigned char arg1;", str(arg1))
        ss = ss.replace("unsigned char arg2;", str(arg2))
        return ss.split()

    def call(self, inst, **kwargs):
        with self.run_challenge(alarm=2, **kwargs) as process:
            process.clean()
            process.write(inst)
            o = process.readall()
            return -1 if process.proc.returncode in [ -14, 124, 142 ] else process.proc.returncode, o

    def verify(self, **kwargs):
        """
        Yan85 full emulator, directly interprets user input as yan85. All opcodes are randomized based on the flag.
        """
        omap = { }
        rmap = { }
        smap = { }

        all_codes = { 1, 2, 4, 8, 16, 32, 64, 128 }

        with self.run_challenge(**kwargs) as process:
            process.write(b"nope")
            o = process.readall()
            assert self.flag not in o

        #print("finding hanging instructions")
        hanging_instructions = set()
        for op in all_codes:
            inst = bytes(int(s) for s in self.arrange_inst(op, '0', '0'))
            if self.call(inst, **kwargs)[0] == -1:
                hanging_instructions.add(op)
        assert len(hanging_instructions) == 2 # sys and stk

        #print("finding exit")
        exits = [ ]
        for op in hanging_instructions:
            for arg1 in all_codes:
                inst = bytes(int(s) for s in self.arrange_inst(op, arg1, '0'))
                if self.call(inst, **kwargs)[0] == 0:
                    #print("YEAH!", op, arg1)
                    exits.append((op, arg1))
        #print(exits)
        assert len(exits) == 1
        omap['INST_SYS'] = exits[0][0]
        smap['SYS_EXIT'] = exits[0][1]

        # non-exit one is stk
        omap['INST_STK'] = next(iter(hanging_instructions - set(omap.values())))

        #print("figuring out valid registers")
        valid_registers = set()
        for arg1 in all_codes:
            inst = bytes(int(s) for s in self.arrange_inst(omap['INST_STK'], arg1, 0))
            #print(inst)
            r,_ = self.call(inst, **kwargs)
            if r == -1:
                valid_registers.add(arg1)
        invalid_register = next(iter(all_codes - valid_registers))
        #print(valid_registers)
        assert len(valid_registers) == 7

        #print("finding jump instruction")
        # it should require a valid register for arg 2 and anything for arg1
        jump_candidates = set()
        for op in all_codes - set(omap.values()):
            inst = bytes(int(s) for s in self.arrange_inst(op, invalid_register, next(iter(valid_registers))))
            r,_ = self.call(inst, **kwargs)
            if r == -1:
                jump_candidates.add(op)
        assert len(jump_candidates) == 1
        omap['INST_JMP'] = next(iter(jump_candidates))
        del jump_candidates, op

        #print("finding imm instruction")
        # it should require a valid register for arg1 and anything for arg2
        imm_candidates = set()
        for op in all_codes - set(omap.values()):
            inst = bytes(int(s) for s in self.arrange_inst(op, next(iter(valid_registers)), invalid_register))
            r,_ = self.call(inst, **kwargs)
            if r == -1:
                imm_candidates.add(op)
        #print(imm_candidates)
        assert len(imm_candidates) == 1
        omap['INST_IMM'] = next(iter(imm_candidates))
        del imm_candidates, op

        #print("finding i by making an infinite loop")
        i_candidates = set()
        for arg1 in valid_registers:
            inst = bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], arg1, '0') + self.arrange_inst(omap['INST_IMM'], invalid_register, '0'))
            r,_ = self.call(inst, **kwargs)
            if r == -1:
                i_candidates.add(arg1)
        assert len(i_candidates) == 1
        rmap['SPEC_REG_I'] = next(iter(i_candidates))
        assert self.call(bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_I'], '0') + self.arrange_inst(omap['INST_IMM'], invalid_register, '0')), **kwargs)[0] == -1
        del i_candidates, arg1

        #print("finding a by exiting")
        a_candidates = set()
        for arg1 in valid_registers - set(rmap.values()):
            inst = bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], arg1, '42') + self.arrange_inst(omap['INST_SYS'], smap['SYS_EXIT'], '0'))
            r,_ = self.call(inst, **kwargs)
            if r == 42:
                a_candidates.add(arg1)
        assert len(a_candidates) == 1
        rmap['SPEC_REG_A'] = next(iter(a_candidates))
        del a_candidates, arg1

        gadget_exit42 = bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_A'], '42') + self.arrange_inst(omap['INST_SYS'], smap['SYS_EXIT'], '0'))
        assert self.call(gadget_exit42, **kwargs)[0] == 42

        # write /flag
        gadget_pushflag = bytes(int(s) for s in (
            self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_A'], ord('/')) +
            self.arrange_inst(omap['INST_STK'], 0, rmap['SPEC_REG_A']) +
            self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_A'], ord('f')) +
            self.arrange_inst(omap['INST_STK'], 0, rmap['SPEC_REG_A']) +
            self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_A'], ord('l')) +
            self.arrange_inst(omap['INST_STK'], 0, rmap['SPEC_REG_A']) +
            self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_A'], ord('a')) +
            self.arrange_inst(omap['INST_STK'], 0, rmap['SPEC_REG_A']) +
            self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_A'], ord('g')) +
            self.arrange_inst(omap['INST_STK'], 0, rmap['SPEC_REG_A']) +

            self.arrange_inst(omap['INST_STK'], rmap['SPEC_REG_A'], 0) +
            self.arrange_inst(omap['INST_STK'], rmap['SPEC_REG_A'], 0) +
            self.arrange_inst(omap['INST_STK'], rmap['SPEC_REG_A'], 0) +
            self.arrange_inst(omap['INST_STK'], rmap['SPEC_REG_A'], 0) +
            self.arrange_inst(omap['INST_STK'], rmap['SPEC_REG_A'], 0)
        ))

        # make sure that that works
        r,_ = self.call(gadget_pushflag + gadget_exit42)
        assert r == 42

        #print("finding sleep")
        sleep_candidates = set()
        for snum in all_codes-set(smap.values()):
            slp = bytes(int(s) for s in (
                self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_A'], '60') +
                self.arrange_inst(omap['INST_SYS'], snum, rmap['SPEC_REG_A'])
            ))
            r,_ = self.call(slp + gadget_exit42, **kwargs)
            assert r in { -1, 42 }
            if r == -1:
                sleep_candidates.add(snum)
        assert len(sleep_candidates) == 1
        smap['SYS_SLEEP'] = next(iter(sleep_candidates))
        del sleep_candidates, snum

        #print("finding write")
        write_candidates = set()
        for snum in all_codes-set(smap.values()):
            # set all unknown registers to 2 (should print out 'fl')
            set_all = b''.join(bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], r, '3')) for r in valid_registers-set(rmap.values()))
            set_a = bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_A'], '1'))
            syscall = bytes(int(s) for s in self.arrange_inst(omap['INST_SYS'], snum, rmap['SPEC_REG_A']))
            r,o = self.call(gadget_pushflag + set_all + set_a + syscall + gadget_exit42)
            if b'lag' in o:
                write_candidates.add(snum)
        assert len(write_candidates) == 1
        smap['SYS_WRITE'] = next(iter(write_candidates))
        del write_candidates, snum

        #print("finding c")
        c_candidates = set()
        for arg1 in valid_registers - set(rmap.values()):
            # set all unknown registers to 2 (should print out 'fl')
            set_all = b''.join(bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], r, '1')) for r in valid_registers-set(rmap.values()))
            set_c = bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], arg1, '5'))
            set_a = bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_A'], '1'))
            syscall = bytes(int(s) for s in self.arrange_inst(omap['INST_SYS'], smap['SYS_WRITE'], rmap['SPEC_REG_A']))
            r,o = self.call(gadget_pushflag + set_all + set_c + set_a + syscall + gadget_exit42)
            if b"/flag" in o:
                c_candidates.add(arg1)
        assert len(c_candidates) == 1
        rmap['SPEC_REG_C'] = next(iter(c_candidates))
        del c_candidates, arg1

        #print("finding b")
        b_candidates = set()
        for arg1 in valid_registers - set(rmap.values()):
            # set all unknown registers to 2 (should print out 'fl')
            set_all = b''.join(bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], r, '0')) for r in valid_registers-set(rmap.values()))
            set_b = bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], arg1, '1'))
            set_c = bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_C'], '1'))
            set_a = bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_A'], '1'))
            syscall = bytes(int(s) for s in self.arrange_inst(omap['INST_SYS'], smap['SYS_WRITE'], rmap['SPEC_REG_A']))
            r,o = self.call(gadget_pushflag + set_all + set_b + set_c + set_a + syscall + gadget_exit42)
            if b'/' in o:
                b_candidates.add(arg1)
        assert len(b_candidates) == 1
        rmap['SPEC_REG_B'] = next(iter(b_candidates))
        del b_candidates, arg1

        #print("###########################")
        #print("###########################")
        #print("###########################")
        #print("###########################")
        #print("Recovered:", omap, rmap, smap)

        # get the flag
        for read_num in all_codes - set(smap.values()):
            for open_num in all_codes - set(smap.values()):
                shellcode = (
                    gadget_pushflag +
                    bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_A'], '1')) +
                    bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_B'], '0')) +
                    bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_C'], '100')) +
                    bytes(int(s) for s in self.arrange_inst(omap['INST_SYS'], open_num, rmap['SPEC_REG_A'])) +
                    bytes(int(s) for s in self.arrange_inst(omap['INST_SYS'], read_num, rmap['SPEC_REG_C'])) +
                    bytes(int(s) for s in self.arrange_inst(omap['INST_IMM'], rmap['SPEC_REG_A'], '1')) +
                    bytes(int(s) for s in self.arrange_inst(omap['INST_SYS'], smap['SYS_WRITE'], rmap['SPEC_REG_C'])) +
                    gadget_exit42
                )
                r,o = self.call(shellcode)
                #print(r,o)
                assert r in { -1, 1, 42 }
                if self.flag in o:
                    return True
        assert False

LEVELS = [
    BabyRevNoMangler,
    BabyRevSwapMangler,
    BabyRevReverseMangler,
    BabyRevSortMangler,
    BabyRevXORMangler,
    BabyRev3Manglers,
    BabyRev5Manglers,
    BabyRev7Manglers,
    BabyRevPatch5Bytes,
    BabyRevPatch1Byte,
    BabyRevPatch2BytesIntegrityCheck,
    BabyRevYan85BasicCReadExpectedMemcmpSuccessExit,
    BabyRevYan85BasicCReadMemcmpSuccessExit,
    BabyRevYan85BasicCMemcmpSuccessExit,
    BabyRevYan85BasicMemcmp,
    BabyRevYan85ManualMemcmp,
    BabyRevYan85Manglers,
    BabyRevYan85MangledMemcmp,
    BabyRevYan85EmulatorBasic,
    BabyRevYan85EmulatorMangled,
    BabyRevYan85EmulatorUserInput,
    BabyRevYan85BlindEmulatorUserInput,
]
NUM_TESTING=1
DOJO_MODULE="reversing"
pwnshop.register_challenges(LEVELS)
