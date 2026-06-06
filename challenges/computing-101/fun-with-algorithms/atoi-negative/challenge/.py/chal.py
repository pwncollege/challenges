import __main__ as checker
import random
import subprocess

# Shared-library challenge: the flag is dispensed by this (root) checker only
# after it independently verifies the value `solve` returned. The harness that
# runs the .so is unprivileged and never holds the flag.
shared = True
give_flag = True

MASK = (1 << 64) - 1
ROUNDS = 6

check_runtime_prologue = "Let's hand your solve() a batch of random numbers --- some negative..."
check_runtime_success = "Every number converted correctly, sign and all!"
check_runtime_failure = "One of those conversions came back wrong:\n"


def gen_case():
    # Decimal digits, sometimes with a leading minus sign.
    n = random.randint(-(2**31), 2**31 - 1)
    return str(n), n


def as_signed(v):
    return v - (1 << 64) if v >= (1 << 63) else v


def run_one(so_path, numstr, *, quiet):
    p = subprocess.run(
        ["/challenge/harness", so_path, numstr],
        stdout=subprocess.PIPE,
        stderr=(subprocess.DEVNULL if quiet else None),
        timeout=5,
    )
    if p.returncode != 0:
        raise AssertionError(
            f"The harness exited abnormally (status {p.returncode}) on input {numstr!r}."
        )
    if len(p.stdout) < 8:
        raise AssertionError("The harness never reported a result --- did your solve crash?")
    return int.from_bytes(p.stdout[-8:], "little")


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f'/challenge/harness {so_path} <number>')
    print("")
    for i in range(ROUNDS):
        numstr, expected = gen_case()
        got = run_one(so_path, numstr, quiet=(i != 0))
        assert got == (expected & MASK), (
            f"atoi({numstr!r}) should be {expected}, but your solve returned {as_signed(got)}."
        )
        if i != 0:
            print(f"  ok: solve({numstr!r}) = {as_signed(got)}")
    return True
