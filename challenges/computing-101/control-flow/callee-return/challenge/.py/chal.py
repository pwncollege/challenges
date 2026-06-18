import __main__ as checker
import os
import random
import signal
import subprocess
import sys

shared = True
give_flag = True
SUCCESS_MARKER = b"callee-return-success\n"

check_runtime_prologue = (
    "Let's load your shared library and call solve(secret) "
    "with a random 64-bit value to see if you return it back..."
)
check_runtime_success = "Your function returned the secret back. The checker will print the flag now!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_runtime(so_path):
    secret = random.randrange(0, 2**64)
    success_read_fd, success_write_fd = os.pipe()
    os.set_blocking(success_read_fd, False)

    print("")
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} {hex(secret)}")
    print("")
    sys.stdout.flush()

    try:
        try:
            result = subprocess.run(
                ["/challenge/harness", so_path, hex(secret), str(success_write_fd)],
                pass_fds=(success_write_fd,),
                timeout=5,
            )
        finally:
            os.close(success_write_fd)
        try:
            success_marker = os.read(success_read_fd, len(SUCCESS_MARKER) + 1)
        except BlockingIOError:
            success_marker = b""
    finally:
        os.close(success_read_fd)
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
    assert success_marker == SUCCESS_MARKER, "The harness exited without confirming a successful return."

    return True
