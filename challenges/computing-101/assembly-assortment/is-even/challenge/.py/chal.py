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

check_runtime_prologue = "Let's hand your solve() a series of values and see if it spots the even ones..."
check_runtime_success = "Every value classified correctly!"
check_runtime_failure = "That didn't come out right:\n"


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
    # The classic slip: returning the raw low bit (n & 1), which is 1 for ODD.
    # We want 1 for EVEN, so the low bit still has to be inverted.
    if got == (x & 1):
        return " That's the parity un-inverted --- `n & 1` is 1 for ODD, so flip the low bit to answer 1 for EVEN."
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <value>")
    print("")
    cases = [0, 1, 2, 3, 4, 0xFF, 0x100, 1 << 63, (1 << 64) - 1]
    cases += [random.randrange(0, 1 << 64) for _ in range(5)]
    for i, x in enumerate(cases):
        got = run_one(so_path, x, quiet=(i != 0))
        want = 1 if x % 2 == 0 else 0
        assert got == want, (
            f"solve({hex(x)}) should be {want} ({'even' if want else 'odd'}), "
            f"but your solve returned {hex(got)}." + diagnose(x, got)
        )
        if i != 0:
            print(f"  ok: solve({hex(x)}) = {got} ({'even' if want else 'odd'})")
    return True
