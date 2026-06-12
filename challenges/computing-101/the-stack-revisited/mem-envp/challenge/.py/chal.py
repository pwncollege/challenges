import __main__ as checker
import signal
import subprocess
import sys

give_flag = False
num_instructions = 8

# envp[0] (the whole "FLAG=<value>" string) is padded to exactly this many
# bytes so the student can write a constant byte count. It is the 5-byte
# "FLAG=" name plus a 128-byte flag field, so any real flag up to 128 bytes
# fits (flags are an implementation detail and DO vary in length -- never
# assume the current length). The student is told this number in DESCRIPTION.md.
FLAG_VAR_LEN = 5 + 128  # len("FLAG=") + 128-byte flag field = 133

check_disassembly_prologue = "Checking that your assembly reads envp[0] and writes its bytes to stdout..."
check_disassembly_success = "Your assembly looks correct! Let's see what it prints..."
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Running your program with FLAG set in the environment..."
check_runtime_success = "If your program is right, the flag is printed above!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_disassembly(disas):
    mov_operands = checker.mov_operands(disas)

    has_envp_deref = any("[rsp + 0x18]" in src for _, src in mov_operands)
    assert has_envp_deref, (
        "You need to dereference rsp with an offset of 24 bytes (using [rsp+24] or [rsp+0x18])\n"
        "to read the envp[0] pointer stored on the stack!\n"
        "Remember: [rsp]=argc, [rsp+8]=argv[0], [rsp+16]=NULL (end of argv), [rsp+24]=envp[0]."
    )

    assert ["rax", "1"] in mov_operands, "You need to set rax to 1, the syscall number for write!"
    assert ["rax", "0x3c"] in mov_operands, "You need to set rax to 60 (0x3c), the syscall number for exit!"

    syscalls = [d for d in disas if d.mnemonic == "syscall"]
    assert len(syscalls) >= 2, "You need two syscalls: one to write envp[0] out, and one to exit!"

    return True


def check_runtime(filename):
    flag = checker.read_flag().rstrip(b"\n")
    prefix = b"FLAG="
    pad_count = FLAG_VAR_LEN - len(prefix) - len(flag)
    assert pad_count >= 0, f"flag too long ({len(flag)} bytes) for FLAG_VAR_LEN={FLAG_VAR_LEN}"
    env_value = (flag + b"=" * pad_count).decode()

    print("")
    checker.print_prompt()
    checker.slow_print(f"env -i 'FLAG=<the flag, padded to {FLAG_VAR_LEN - len(prefix)} bytes>' {filename}")
    print("")
    sys.stdout.flush()

    result = subprocess.run(
        ["env", "-i", f"FLAG={env_value}", filename],
        timeout=5,
    )
    print("")

    if result.returncode < 0:
        signum = -result.returncode
        signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
        # Mirror what an interactive bash prints when a foreground job dies.
        sys.stderr.write(("Segmentation fault" if signum == signal.SIGSEGV else signame) + "\n")
        sys.stderr.flush()
        raise AssertionError(f"Your program crashed with {signame}.")

    return True
