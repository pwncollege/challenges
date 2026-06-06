import __main__ as checker
import random
import subprocess

# Shared-library challenge: the flag is dispensed by this (root) checker only
# after it independently verifies the value `solve` returned. The harness that
# runs the .so is unprivileged and never holds the flag.
shared = True
give_flag = True

MASK = (1 << 64) - 1
ROUNDS = 8

# Non-digit bytes used to terminate (and trail) the number. No '-' here, so it
# can never be mistaken for a leading sign of the *next* (nonexistent) number.
JUNK = "abcXYZ!.,;:/ +=_()@%"

check_runtime_prologue = "Let's hand your solve() numbers buried in trailing junk..."
check_runtime_success = "You stopped at the right spot every time!"
check_runtime_failure = "One of those conversions came back wrong:\n"


def gen_case():
    n = random.randint(-(2**31), 2**31 - 1)
    s = str(n)
    if random.random() < 0.8:
        # Append a non-digit, then arbitrary trailing characters that solve must ignore.
        s += random.choice(JUNK)
        s += "".join(random.choice(JUNK + "0123456789") for _ in range(random.randint(0, 5)))
    return s, n


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
    checker.slow_print(f'/challenge/harness {so_path} <number-then-junk>')
    print("")
    for i in range(ROUNDS):
        numstr, expected = gen_case()
        got = run_one(so_path, numstr, quiet=(i != 0))
        assert got == (expected & MASK), (
            f"atoi({numstr!r}) should be {expected} (stop at the first non-digit), "
            f"but your solve returned {as_signed(got)}."
        )
        if i != 0:
            print(f"  ok: solve({numstr!r}) = {as_signed(got)}")
    return True
