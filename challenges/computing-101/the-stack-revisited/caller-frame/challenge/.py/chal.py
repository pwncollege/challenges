import __main__ as checker
import subprocess

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

    subprocess.run(
        ["/challenge/harness", so_path],
        input=flag_buf,
        timeout=5,
    )
    print("")

    return True
