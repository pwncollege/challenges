import __main__ as checker
import signal
import subprocess
import sys

shared = True
give_flag = False

check_runtime_prologue = (
    "Let's load your library and run solve(check_callee_clobbered) --- "
    "with my values sitting in rbx,r12,r13,r14,r15..."
)
check_runtime_success = "If you used those registers and then restored them, the flag is printed above!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_runtime(so_path):
    flag = checker.read_flag()  # raw bytes, handed to the harness on stdin (not argv)

    print("")
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path}")
    print("")
    sys.stdout.flush()

    result = subprocess.run(
        ["/challenge/harness", so_path],
        input=flag,
        timeout=5,
    )
    print("")

    if result.returncode != 0:
        if result.returncode < 0:
            signum = -result.returncode
            signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
            sys.stderr.write(("Segmentation fault" if signum == signal.SIGSEGV else signame) + "\n")
            sys.stderr.flush()
            raise AssertionError(f"The harness crashed with {signame}.")
        raise AssertionError("Your solve did not satisfy the check (the harness released no flag).")

    return True
