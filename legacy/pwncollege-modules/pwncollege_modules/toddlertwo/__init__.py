import subprocess
import pwnshop
import pwn
import sys

PWNSHOP_AUTOREGISTER = False

from pwnshop import Challenge, KernelChallenge, retry
from ..babyrev import assembler


class ToddlerTwoKernelBase(KernelChallenge):
    TEMPLATE_PATH = "toddlertwo/kernel_yan85.c"

    device_permissions = "0600"

    remote_code = True
    read_overflow = True
    write_overflow = True
    yan85_seccomp = True

    difficulty = None
    memory_size = 256
    memory = "\0"*256
    prerandomize = True
    rerandomize = False
    interpreted = True
    interpret_forever = True
    operand_type = "unsigned char"
    word_type = "unsigned char"

    # prerandomization
    inst_definition = None
    register_order = None
    operation_order = None
    syscall_order = None
    flag_order = None

    def _shift_by(self, list_name, index):
        lst = getattr(self, list_name)
        return hex(1 << lst.index(index))

    def randomize(self, operand_type="unsigned char", force_space_sys=False):
        # randomize
        assembler.INSTRUCTION_ORDER.sort()
        assembler.SYSCALL_ORDER.sort()
        assembler.ENCODING_ORDER.sort()
        assembler.REG_ORDER.sort()
        assembler.FLAG_ORDER.sort()
        self.random.shuffle(assembler.INSTRUCTION_ORDER)
        self.random.shuffle(assembler.SYSCALL_ORDER)
        self.random.shuffle(assembler.ENCODING_ORDER)
        self.random.shuffle(assembler.REG_ORDER)
        self.random.shuffle(assembler.FLAG_ORDER)

        # for toddler, we want a level where the syscall opcode is a space (for scanf)
        if force_space_sys:
            sys_index = assembler.INSTRUCTION_ORDER.index("sys")
            assembler.INSTRUCTION_ORDER[5], assembler.INSTRUCTION_ORDER[sys_index] = "sys", assembler.INSTRUCTION_ORDER[5]

        # save to the template
        self.inst_definition = f"""{{ {operand_type} {assembler.ENCODING_ORDER[0]}; {operand_type} {assembler.ENCODING_ORDER[1]}; {operand_type} {assembler.ENCODING_ORDER[2]}; }}"""
        self.register_order = assembler.REG_ORDER
        self.operation_order = assembler.INSTRUCTION_ORDER
        self.syscall_order = assembler.SYSCALL_ORDER
        self.flag_order = assembler.FLAG_ORDER

        # generate encodings for later assembling
        assembler.ENCODING.clear()
        assembler.generate_encoding()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.prerandomize:
            self.randomize(operand_type=self.operand_type)


class ToddlerTwoUserspaceBase(Challenge):
    TEMPLATE_PATH = "toddlertwo/toddlertwo_userspace.c"
    LINK_LIBRARIES = ["seccomp", "pthread"]

    stack_goodbye = True

    threaded_server = None
    fork_server = None
    atomic_ypu = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.syscalls_allowed = ["read", "write", "close", "ioctl", "accept", "clone", "set_robust_list", "futex"]
        if self.threaded_server:
            self.syscalls_allowed += ["mmap", "munmap", "mprotect", "fcntl", "madvise", "exit"]
        else:
            self.syscalls_allowed += ["dup2", "wait4", "exit_group"]


class ToddlerTwoLevel1(ToddlerTwoKernelBase):
    ""

    device_permissions = "0666"
    yan85_seccomp = False

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs):
            yan85_program = assembler.finalize(
                [
                    *assembler.store_constant(0x80, b"/flag"),
                    *assembler.open_file(0x80, save=""),
                    *assembler.store_constant(0x80, b"/tmp/test"),
                    *assembler.open_file(0x80, flags=1, save=""),
                    *assembler.read_bytes(0x80, 0xFF, fd="0", save=""),
                    *assembler.print_stored(0x80, "d", save=""),
                    *assembler.vm_exit(42),
                ]
            )
            encoded_program = "".join(
                f"\\x{hex(e).replace('x', '')[-2:]}" for e in yan85_program
            )

            self.run_sh("touch /tmp/test").wait()

            result = self.run_c(
                f"""
                #include <unistd.h>
                #include <fcntl.h>
                #include <stdio.h>
                #include <string.h>
                #include <sys/mman.h>
                #include <sys/ioctl.h>
                int main()
                {{
                    setvbuf(stdin, NULL, _IONBF, 0);
                    setvbuf(stdout, NULL, _IONBF, 0);

                    int fd = open("/proc/ypu", O_RDWR);
                    printf("fd %d\\n", fd);
                    char *ptr = mmap(0, 0x1000, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
                    printf("PTR %p\\n", ptr);

                    memcpy(ptr, "{encoded_program}", {len(yan85_program)});

                    ioctl(fd, 1337, 0);
                }}
                """,
            ).readall()

            assert self.flag in self.run_sh(f"cat /tmp/test").readall()


class ToddlerTwoLevel1Userspace(Challenge):
    ""

    TEMPLATE_PATH = "babykernel/babykernel_userspace.c"
    LINK_LIBRARIES = ["capstone", "seccomp"]
    PIE = False

    shellcode = True
    open_device = True
    syscalls_allowed = ["mmap", "ioctl"]
    device_path = "/proc/ypu"


class ToddlerTwoLevel2(ToddlerTwoKernelBase):
    ""

    def verify(self, **kwargs):
        """
        TBD
        """
        with self.run_challenge(**kwargs):
            yan85_program = assembler.finalize(
                [
                    *assembler.store_constant(0x80, b"/flag"),
                    *assembler.open_file(0x80, save=""),
                    *assembler.store_constant(0x80, b"/tmp/test"),
                    *assembler.open_file(0x80, flags=1, save=""),
                    *assembler.read_bytes(0x80, 0xFF, fd="0", save=""),
                    *assembler.print_stored(0x80, "d", save=""),
                    *assembler.vm_exit(42),
                ]
            )
            encoded_program = "".join(
                f"\\x{hex(e).replace('x', '')[-2:]}" for e in yan85_program
            )

            self.run_sh("touch /tmp/test").wait()

            result = self.run_c(
                f"""
                #include <unistd.h>
                #include <fcntl.h>
                #include <stdio.h>
                #include <string.h>
                #include <sys/mman.h>
                #include <sys/ioctl.h>
                int main()
                {{
                    setvbuf(stdin, NULL, _IONBF, 0);
                    setvbuf(stdout, NULL, _IONBF, 0);

                    int fd = open("/proc/ypu", O_RDWR);
                    printf("fd %d\\n", fd);
                    char *ptr = mmap(0, 0x1000, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
                    printf("PTR %p\\n", ptr);

                    memcpy(ptr, "{encoded_program}", {len(yan85_program)});

                    ioctl(fd, 1337, 0);
                }}
                """,
            ).readall()

            assert b"Machine ABORTED due to: secure computation violation" in self.run_sh("dmesg").readall()

            # TODO: exploit, hopefully this race isn't so bad


class ToddlerTwoLevel2Userspace(ToddlerTwoLevel1Userspace):
    ""

    syscalls_allowed = ["mmap", "ioctl", "fork"]


class ToddlerTwoLevel3(ToddlerTwoKernelBase):
    ""


class ToddlerTwoLevel3Userspace(ToddlerTwoUserspaceBase):
    ""

    threaded_server = True


class ToddlerTwoLevel4(ToddlerTwoKernelBase):
    ""


class ToddlerTwoLevel4Userspace(ToddlerTwoUserspaceBase):
    ""

    threaded_server = True
    atomic_ypu = True


class ToddlerTwoLevel5(ToddlerTwoKernelBase):
    ""


class ToddlerTwoLevel5Userspace(ToddlerTwoUserspaceBase):
    ""

    EXEC_STACK = True
    CANARY = False

    fork_server = True
    local_programs = True


class ToddlerTwoLevel6(ToddlerTwoKernelBase):
    ""


class ToddlerTwoLevel6Userspace(ToddlerTwoUserspaceBase):
    ""

    EXEC_STACK = True
    CANARY = True

    fork_server = True
    local_programs = True


class ToddlerTwoLevel7(ToddlerTwoKernelBase):
    ""

    yan85_seccomp_harden = True


class ToddlerTwoLevel7Userspace(ToddlerTwoUserspaceBase):
    ""

    EXEC_STACK = True
    CANARY = True

    fork_server = True
    local_programs = True


class ToddlerTwoLevel8(ToddlerTwoKernelBase):
    ""

    KASLR = True
    yan85_seccomp_harden = True


class ToddlerTwoLevel8Userspace(ToddlerTwoUserspaceBase):
    ""

    EXEC_STACK = True
    CANARY = True

    fork_server = True
    local_programs = True


LEVELS = [
    ToddlerTwoLevel1,
    ToddlerTwoLevel2,
    ToddlerTwoLevel3,
    ToddlerTwoLevel4,
    ToddlerTwoLevel5,
    ToddlerTwoLevel6,
    ToddlerTwoLevel7,
    ToddlerTwoLevel8,
]
NUM_TESTING=1
DOJO_MODULE="exploitation2"
pwnshop.register_challenges(LEVELS)
