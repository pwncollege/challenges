import __main__ as checker
import signal
import subprocess
import sys

give_flag = False
num_instructions = 8

FLAG_VAR_LEN = 64  # envp[0] string is padded to exactly this many bytes

check_disassembly_prologue = "Checking that your assembly reads envp[0] and writes its bytes to stdout..."
check_disassembly_success = "Your assembly looks correct! Let's see what it prints..."
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Running your program with FLAG set in the environment..."
check_runtime_success = "If your program is right, the flag is printed above!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_disassembly(disas):
    mov_operands = [d.op_str.split(", ") for d in disas if d.mnemonic == "mov"]

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

    # Direct subprocess (no bash -c) so the FLAG=... value never appears in a
    # bash signal message on a deliberately-broken solve. On a signal exit we
    # surface the signal name ourselves via AssertionError below.
    result = subprocess.run(
        ["env", "-i", f"FLAG={env_value}", filename],
        timeout=5,
    )
    print("")

    if result.returncode < 0:
        signum = -result.returncode
        signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
        raise AssertionError(f"Your program crashed with {signame}.")

    return True
