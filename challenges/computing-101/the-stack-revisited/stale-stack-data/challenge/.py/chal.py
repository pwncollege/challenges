import __main__ as checker
import signal
import subprocess
import sys

shared = True
give_flag = False
solve_symbol = "solve"

# Fixed-size flag field. The flag is padded to exactly this many bytes so the
# student can write a constant byte count; it must be large enough to hold any
# real flag (flags are an implementation detail and DO vary in length -- never
# assume the current length). Keep in sync with FLAG_LEN in harness.c and the
# copy count in read_flag.S.
FLAG_BUF_LEN = 128

check_runtime_prologue = (
    "Let's see if your solve calls read_flag, then steals the stale stack bytes "
    "it leaves behind..."
)
check_runtime_success = "If your solve is right, your code printed the flag."
check_runtime_failure = "Hmm, that's not right:\n"


def check_runtime(so_path):
    flag = checker.read_flag().rstrip(b"\n")
    pad_count = FLAG_BUF_LEN - len(flag)
    assert pad_count >= 0, f"flag too long ({len(flag)} bytes) for FLAG_BUF_LEN={FLAG_BUF_LEN}"
    flag_buf = flag + b"=" * pad_count

    print("")
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path}")
    print("")
    sys.stdout.flush()

    try:
        result = subprocess.run(
            ["/challenge/harness", so_path],
            input=flag_buf,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError("solve() never returned. Make sure your function reaches `ret`.")
    print("")

    if result.returncode < 0:
        signum = -result.returncode
        signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
        sys.stderr.write(("Segmentation fault" if signum == signal.SIGSEGV else signame) + "\n")
        sys.stderr.flush()
        raise AssertionError(f"The harness crashed with {signame}.")

    if result.returncode == 1:
        raise AssertionError("Your solve returned without calling the read_flag function pointer.")
    assert result.returncode == 0, f"The harness exited abnormally (status {result.returncode})."

    return True
