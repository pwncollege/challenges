import __main__ as checker
import signal
import subprocess
import sys

shared = True
give_flag = False

check_runtime_prologue = (
    "Let's load your shared library and call solve(callback) --- "
    "the callback expects 1337 as its argument..."
)
check_runtime_success = "If you called the callback with 1337, the flag is printed above!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_runtime(so_path):
    flag = checker.read_flag().rstrip(b"\n")

    print("")
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path}")
    print("")
    sys.stdout.flush()

    try:
        result = subprocess.run(
            ["/challenge/harness", so_path],
            input=flag,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError("The harness did not finish within 5 seconds. Make sure your solve returns.") from None
    print("")

    if result.returncode < 0:
        signum = -result.returncode
        signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
        # Mirror what an interactive bash prints when a foreground job dies.
        sys.stderr.write(("Segmentation fault" if signum == signal.SIGSEGV else signame) + "\n")
        sys.stderr.flush()
        raise AssertionError(f"The harness crashed with {signame}.")

    if result.returncode == 1:
        raise AssertionError("Your solve did not call the callback with the required argument.")
    assert result.returncode == 0, f"The harness exited abnormally (status {result.returncode})."

    return True
