import __main__ as checker
import random
import subprocess

# A shared-library challenge: the learner submits `atoi` inside a .so, and the
# flag is dispensed by this (root) checker only after it independently verifies
# the value `atoi` returned. The harness that actually runs the .so is
# unprivileged and never holds the flag.
shared = True
give_flag = True
solve_symbol = "atoi"  # this level's entrypoint is named atoi

MASK = (1 << 64) - 1
ROUNDS = 6

check_runtime_prologue = "Let's hand your atoi() a batch of random numbers, as text..."
check_runtime_success = "Every number converted correctly!"
check_runtime_failure = "One of those conversions came back wrong:\n"


def gen_case():
    # A clean run of decimal digits: no sign, no trailing junk.
    n = random.randint(0, 2**31 - 1)
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
    # The harness writes its 8-byte result last, so the tail is what atoi returned.
    return int.from_bytes(p.stdout[-8:], "little")


def diagnose(numstr, got):
    g = as_signed(got)
    if g == sum(int(c) for c in numstr):
        return " That's the sum of the digits --- multiply the running total by 10 before adding each new digit."
    acc = 0
    for c in numstr:
        acc = (acc * 10 + ord(c)) & MASK
    if got == acc:
        return " Those are the ASCII codes accumulated --- subtract '0' from each character before adding it."
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f'/challenge/harness {so_path} <number>')
    print("")
    for i in range(ROUNDS):
        numstr, expected = gen_case()
        got = run_one(so_path, numstr, quiet=(i != 0))
        assert got == (expected & MASK), (
            f"atoi({numstr!r}) should be {expected}, but your atoi returned {as_signed(got)}."
            + diagnose(numstr, got)
        )
        if i != 0:
            print(f"  ok: atoi({numstr!r}) = {as_signed(got)}")
    return True
