import __main__ as checker
import subprocess

shared = True
give_flag = False

check_runtime_prologue = (
    "Let's load your shared library and call solve(callback) --- "
    "the callback expects 1337 as its argument..."
)
check_runtime_success = "If you called the callback with 1337, the flag is printed above!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_runtime(so_path):
    flag = checker.read_flag().rstrip(b"\n").decode()

    print("")
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <flag>")
    print("")

    subprocess.run(
        ["/challenge/harness", so_path, flag],
        timeout=5,
    )
    print("")

    return True
