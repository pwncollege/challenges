import __main__ as checker
import random
import subprocess

# Shared-library challenge: the learner submits `solve` inside a .so. The flag is
# dispensed by this (root) checker only after it independently verifies the
# values solve() returns. The harness that runs the .so is unprivileged and
# never holds the flag.
shared = True
give_flag = True
solve_symbol = "solve"

check_runtime_prologue = "Let's call your solve() and pull byte 1 (bits 8-15) out of each value..."
check_runtime_success = "Every byte extracted correctly!"
check_runtime_failure = "That didn't come out right:\n"


def as_signed(v):
    return v - (1 << 64) if v >= (1 << 63) else v


def want_of(x):
    return (x >> 8) & 0xFF


def run_one(so_path, x, *, quiet):
    try:
        p = subprocess.run(
            ["/challenge/harness", so_path, hex(x)],
            stdout=subprocess.PIPE,
            stderr=(subprocess.DEVNULL if quiet else None),
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            f"solve({hex(x)}) never returned --- it ran too long and was killed. "
            "A function has to reach a `ret`."
        )
    if p.returncode != 0:
        raise AssertionError(f"The harness exited abnormally (status {p.returncode}) on solve({hex(x)}).")
    if len(p.stdout) < 8:
        raise AssertionError("The harness never reported a result --- did your solve crash?")
    return int.from_bytes(p.stdout[-8:], "little")


def diagnose(x, got):
    if got == (x & 0xFF):
        return " That's byte 0 (the lowest byte) --- shift right by 8 first to bring byte 1 down."
    if got == (x >> 8):
        return " You shifted but didn't mask --- finish with `and rax, 0xff` to keep just that byte."
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <value>")
    print("")
    cases = [0x0000, 0x1300, 0xFF00, 0xABCD, 0xDEADBEEF, (1 << 64) - 1]
    cases += [random.randrange(0, 1 << 64) for _ in range(5)]
    for i, x in enumerate(cases):
        got = run_one(so_path, x, quiet=(i != 0))
        want = want_of(x)
        assert got == want, (
            f"solve({hex(x)}) should be {hex(want)}, but your solve returned {hex(got)}."
            + diagnose(x, got)
        )
        if i != 0:
            print(f"  ok: solve({hex(x)}) = {hex(got)}")
    return True
