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

SHIFT = 4
MASK64 = (1 << 64) - 1

check_runtime_prologue = "Let's call your solve() and watch it shift each value left by 4 bits..."
check_runtime_success = "Every value shifted correctly!"
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
    if got == x:
        return " That's the input unchanged --- shift it with `shl rax, 4`."
    if got == (x >> SHIFT):
        return " That shifted the wrong way --- `shl` moves bits left (toward the high end), not right."
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <value>")
    print("")
    cases = [0x0, 0x1, 0x3, 0xFF, 0x1234]
    cases += [random.randrange(0, 1 << 56) for _ in range(5)]
    for i, x in enumerate(cases):
        got = run_one(so_path, x, quiet=(i != 0))
        want = (x << SHIFT) & MASK64
        assert got == want, (
            f"solve({hex(x)}) should be {hex(want)}, but your solve returned {hex(got)}."
            + diagnose(x, got)
        )
        if i != 0:
            print(f"  ok: solve({hex(x)}) = {hex(got)}")
    return True
