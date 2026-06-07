import __main__ as checker
import random
import subprocess

# Shared-library challenge: the flag is dispensed by this (root) checker only
# after it independently verifies the value `atoi` returned. The harness that
# runs the .so is unprivileged and never holds the flag.
shared = True
give_flag = True
solve_symbol = "atoi"  # this level's entrypoint is named atoi

MASK = (1 << 64) - 1
ROUNDS = 6

check_runtime_prologue = "Let's hand your atoi() a batch of random numbers --- some negative..."
check_runtime_success = "Every number converted correctly, sign and all!"
check_runtime_failure = "One of those conversions came back wrong:\n"


def gen_case(sign=None):
    # Decimal digits. `sign` forces the sign path so coverage isn't left to chance.
    if sign == "-":
        n = random.randint(-(2**31), -1)
    elif sign == "+":
        n = random.randint(0, 2**31 - 1)
    else:
        n = random.randint(-(2**31), 2**31 - 1)
    return str(n), n


def as_signed(v):
    return v - (1 << 64) if v >= (1 << 63) else v


def run_one(so_path, numstr, *, quiet):
    try:
        p = subprocess.run(
            ["/challenge/harness", so_path, numstr],
            stdout=subprocess.PIPE,
            stderr=(subprocess.DEVNULL if quiet else None),
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            f"atoi({numstr!r}) never returned --- it ran too long and was killed. "
            "If the loop doesn't advance the pointer (inc rdi) and stop at the terminator, it spins forever."
        )
    if p.returncode != 0:
        raise AssertionError(
            f"The harness exited abnormally (status {p.returncode}) on input {numstr!r}."
        )
    if len(p.stdout) < 8:
        raise AssertionError("The harness never reported a result --- did your atoi crash?")
    return int.from_bytes(p.stdout[-8:], "little")


def diagnose(numstr, expected, got):
    g = as_signed(got)
    neg = numstr.startswith("-")
    body = numstr[1:] if neg else numstr
    if expected < 0 and g == -expected:
        return " Right magnitude, wrong sign --- when the string starts with '-', remember to negate the result."
    ds = sum(int(c) for c in body)
    if g == (-ds if neg else ds):
        return " That's the sum of the digits --- multiply the running total by 10 as you go."
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f'/challenge/harness {so_path} <number>')
    print("")
    # Always exercise both sign paths: round 0 negative, round 1 non-negative,
    # the rest random. (Otherwise ~1 in 64 runs would be all-nonnegative and a
    # sign-ignoring solve could pass the level whose whole point is the sign.)
    forced = {0: "-", 1: "+"}
    for i in range(ROUNDS):
        numstr, expected = gen_case(forced.get(i))
        got = run_one(so_path, numstr, quiet=(i != 0))
        assert got == (expected & MASK), (
            f"atoi({numstr!r}) should be {expected}, but your atoi returned {as_signed(got)}."
            + diagnose(numstr, expected, got)
        )
        if i != 0:
            print(f"  ok: atoi({numstr!r}) = {as_signed(got)}")
    return True
