import __main__ as checker
import shlex
import signal
import subprocess
import sys

shared = True
give_flag = False

FLAG_BUF_LEN = 64  # bytes that caller copies into its frame

check_runtime_prologue = (
    "Let's see if your solve reads the flag out of the caller's frame "
    "and writes it to stdout..."
)
check_runtime_success = "If your solve is right, the flag is printed above!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_runtime(so_path):
    flag = checker.read_flag().rstrip(b"\n")
    pad_count = FLAG_BUF_LEN - len(flag)
    assert pad_count >= 0, f"flag too long ({len(flag)} bytes) for FLAG_BUF_LEN={FLAG_BUF_LEN}"
    flag_buf = flag + b"=" * pad_count  # exactly FLAG_BUF_LEN bytes

    print("")
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path}")
    print("")
    sys.stdout.flush()

    # `bash -c 'cmd; exit $?'` keeps bash alive past a SIGSEGV in the child
    # so it prints its natural "Segmentation fault" message + reports 139.
    inner = "/challenge/harness " + shlex.quote(so_path)
    result = subprocess.run(
        ["bash", "-c", f"{inner}; exit $?"],
        input=flag_buf,
        timeout=5,
    )
    print("")

    if 128 < result.returncode < 192:
        signum = result.returncode - 128
        signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
        raise AssertionError(f"The harness crashed with {signame}.")

    return True
