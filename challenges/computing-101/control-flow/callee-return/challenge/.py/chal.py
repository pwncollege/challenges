import __main__ as checker
import random
import shlex
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
    flag = checker.read_flag().rstrip(b"\n")
    secret = random.randrange(0, 2**64)

    print("")
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} {hex(secret)}   # flag piped via stdin")
    print("")
    sys.stdout.flush()

    # `bash -c 'cmd; exit $?'` keeps bash alive past a SIGSEGV in the child
    # so it prints its natural "Segmentation fault" message + reports 139.
    # Flag goes via stdin so it never appears in the bash-displayed command.
    inner = "/challenge/harness " + " ".join(shlex.quote(a) for a in (so_path, hex(secret)))
    result = subprocess.run(
        ["bash", "-c", f"{inner}; exit $?"],
        input=flag,
        timeout=5,
    )
    print("")

    if 128 < result.returncode < 192:
        signum = result.returncode - 128
        signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
        hint = " (probably because your function fell off the end without `ret`)" if signum == signal.SIGSEGV else ""
        raise AssertionError(f"The harness crashed with {signame}{hint}.")

    return True
