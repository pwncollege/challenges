import __main__ as checker
import subprocess
import sys

shared = True
give_flag = False

check_runtime_prologue = (
    "Let's load your shared library and call solve(callback). "
    "If you call the callback, it'll print the flag for you..."
)
check_runtime_success = "If your solve called the callback, the flag is printed above!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_runtime(so_path):
    flag = checker.read_flag().rstrip(b"\n").decode()

    print("")
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <flag>")
    print("")
    sys.stdout.flush()

    subprocess.run(
        ["/challenge/harness", so_path, flag],
        timeout=5,
    )
    print("")

    return True
