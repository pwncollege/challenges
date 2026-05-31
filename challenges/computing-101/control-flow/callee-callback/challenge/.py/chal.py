import __main__ as checker
import shlex
import signal
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
    flag = checker.read_flag().rstrip(b"\n")

    print("")
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path}   # flag piped via stdin")
    print("")
    sys.stdout.flush()

    # `bash -c 'cmd; exit $?'` keeps bash alive past a SIGSEGV in the child
    # so it prints its natural "Segmentation fault" message + reports 139.
    # Flag goes via stdin so it never appears in the bash-displayed command.
    inner = "/challenge/harness " + shlex.quote(so_path)
    result = subprocess.run(
        ["bash", "-c", f"{inner}; exit $?"],
        input=flag,
        timeout=5,
    )
    print("")

    if 128 < result.returncode < 192:
        signum = result.returncode - 128
        signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
        raise AssertionError(f"The harness crashed with {signame}.")

    return True
