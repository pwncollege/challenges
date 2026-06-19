import __main__ as checker
import os
import random
import signal
import subprocess
import sys

shared = True
give_flag = True
SUCCESS_MARKER = b"stale-stack-value-success\n"

check_runtime_prologue = (
    "Let's see if your solve calls load_secret, then returns the stale "
    "8-byte value it leaves behind..."
)
check_runtime_success = "Your function returned the stale secret. The checker will print the flag now!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_runtime(so_path):
    secret = random.randrange(0, 2**64)
    success_read_fd, success_write_fd = os.pipe()

    print("")
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path}")
    print("")
    sys.stdout.flush()

    try:
        try:
            result = subprocess.run(
                ["/challenge/harness", so_path, str(success_write_fd)],
                input=secret.to_bytes(8, "little"),
                pass_fds=(success_write_fd,),
                timeout=5,
            )
        except subprocess.TimeoutExpired:
            raise AssertionError("solve() never returned. Make sure your function reaches `ret`.") from None
        finally:
            os.close(success_write_fd)
        success_marker = os.read(success_read_fd, len(SUCCESS_MARKER) + 1)
    finally:
        os.close(success_read_fd)
    print("")

    if result.returncode < 0:
        signum = -result.returncode
        signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
        sys.stderr.write(("Segmentation fault" if signum == signal.SIGSEGV else signame) + "\n")
        sys.stderr.flush()
        raise AssertionError(f"The harness crashed with {signame}.")

    if result.returncode == 1:
        raise AssertionError("Your solve returned the wrong value or never called load_secret.")
    assert result.returncode == 0, f"The harness exited abnormally (status {result.returncode})."
    assert success_marker == SUCCESS_MARKER, "The harness exited without confirming a successful stale-value read."

    return True
