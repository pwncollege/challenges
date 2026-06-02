import __main__ as checker
import random
import signal
import subprocess
import sys

shared = True
give_flag = False

check_runtime_prologue = (
    "Let's load your shared library and call solve(secret) "
    "with a random 64-bit value to see if you return it back..."
)
check_runtime_success = "If your function returned the secret back, the flag is printed above!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_runtime(so_path):
    flag = checker.read_flag().rstrip(b"\n").decode()
    secret = random.randrange(0, 2**64)

    print("")
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} {hex(secret)} <flag>")
    print("")
    sys.stdout.flush()

    result = subprocess.run(
        ["/challenge/harness", so_path, hex(secret), flag],
        timeout=5,
    )
    print("")

    if result.returncode < 0:
        signum = -result.returncode
        signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
        # Mirror what an interactive bash prints when a foreground job dies.
        sys.stderr.write(("Segmentation fault" if signum == signal.SIGSEGV else signame) + "\n")
        sys.stderr.flush()
        hint = " (probably because your function fell off the end without `ret`)" if signum == signal.SIGSEGV else ""
        raise AssertionError(f"The harness crashed with {signame}{hint}.")

    return True
