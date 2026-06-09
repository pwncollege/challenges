import __main__ as checker
import random
import subprocess

# Shared-library challenge: the learner submits `LOBYTE` inside a .so. The flag is
# dispensed by this (root) checker only after it independently verifies the
# values LOBYTE() returns. The harness that runs the .so is unprivileged and
# never holds the flag.
shared = True
give_flag = True
solve_symbol = "LOBYTE"

MASK = 0xFF

check_runtime_prologue = "Let's call your LOBYTE() on a series of values and keep only the low byte..."
check_runtime_success = "Every value masked correctly!"
check_runtime_failure = "That didn't come out right:\n"


def as_signed(v):
    return v - (1 << 64) if v >= (1 << 63) else v


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
    if got == x and x != (x & MASK):
        return " That's the input unchanged --- mask it with `and rax, 0xff` to keep only the low 8 bits."
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <value>")
    print("")
    cases = [0x00, 0xFF, 0x100, 0x1337, 0xDEADBEEF, (1 << 64) - 1]
    cases += [random.randrange(0, 1 << 64) for _ in range(5)]
    for i, x in enumerate(cases):
        got = run_one(so_path, x, quiet=(i != 0))
        want = x & MASK
        assert got == want, (
            f"solve({hex(x)}) should be {hex(want)}, but your solve returned {hex(got)}."
            + diagnose(x, got)
        )
        if i != 0:
            print(f"  ok: solve({hex(x)}) = {hex(got)}")
    return True
