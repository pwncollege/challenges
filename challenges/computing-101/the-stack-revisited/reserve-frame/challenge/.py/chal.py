import __main__ as checker
import signal
import subprocess
import sys

shared = True
give_flag = True
solve_symbol = "solve"

check_disassembly_prologue = "Checking that your solve() reserves and restores a stack frame..."
check_disassembly_success = "Your code makes room on the stack and puts rsp back."
check_disassembly_failure = "There's an issue with the frame setup:\n"

check_runtime_prologue = "Let's pre-fill your frame with nonzero bytes and see if solve() clears them..."
check_runtime_success = "Every byte in the reserved frame was cleared."
check_runtime_failure = "That frame was not fully initialized:\n"


def _find_stack_adjust(disas, mnemonic, start=0):
    for idx, insn in enumerate(disas[start:], start):
        if insn.mnemonic == mnemonic and insn.op_str == "rsp, 0x100":
            return idx
    return None


def check_disassembly(disas):
    sub_idx = _find_stack_adjust(disas, "sub")
    assert sub_idx is not None, "Reserve 256 bytes with `sub rsp, 256` before using your frame."

    add_idx = _find_stack_adjust(disas, "add", sub_idx + 1)
    assert add_idx is not None, "Restore the stack pointer with `add rsp, 256` before returning."

    return True


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path}")
    print("")

    try:
        p = subprocess.run(
            ["/challenge/harness", so_path],
            stdout=subprocess.PIPE,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            "solve() never returned. Make sure your initialization loop finishes and your function reaches `ret`."
        )

    if p.returncode < 0:
        signum = -p.returncode
        signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
        sys.stderr.write(("Segmentation fault" if signum == signal.SIGSEGV else signame) + "\n")
        sys.stderr.flush()
        raise AssertionError(
            f"The harness crashed with {signame}. "
            "Before `ret`, `rsp` must point back at the saved return address."
        )

    if p.returncode == 1:
        raise AssertionError(
            "The harness found bytes in the reserved 256-byte frame that were still nonzero. "
            "Clear every byte from `[rsp]` through `[rsp+255]` before restoring `rsp`."
        )
    assert p.returncode == 0, f"The harness exited abnormally (status {p.returncode})."

    return True
