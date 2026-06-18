import __main__ as checker
import random
import signal
import subprocess
import sys

shared = True
give_flag = True

check_runtime_prologue = (
    "Let's load your shared library and call solve(secret) "
    "with a random 64-bit value to see if you return it back..."
)
check_runtime_success = "Your function returned the secret back. The checker will print the flag now!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_runtime(so_path):
    secret = random.randrange(0, 2**64)

    print("")
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} {hex(secret)}")
    print("")
    sys.stdout.flush()

    result = subprocess.run(
        ["/challenge/harness", so_path, hex(secret)],
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

    if result.returncode == 1:
        raise AssertionError("Your function returned the wrong value.")
    assert result.returncode == 0, f"The harness exited abnormally (status {result.returncode})."

    return True
