import __main__ as checker
import random
import subprocess
import sys

# Shared-library challenge: the flag is dispensed by this (root) checker only
# after it independently verifies the value `atoi` returned. The harness that
# runs the .so is unprivileged and never holds the flag.
shared = True
give_flag = True
solve_symbol = "atoi"  # this level's entrypoint is named atoi

MASK = (1 << 64) - 1
ROUNDS = 8

# Non-digit bytes used to terminate (and trail) the number. No '-' here, so it
# can never be mistaken for a leading sign of the *next* (nonexistent) number.
JUNK = "abcXYZ!.,;:/ +=_()@%"

check_runtime_prologue = "Let's hand your atoi() numbers buried in trailing junk..."
check_runtime_success = "You stopped at the right spot every time!"
check_runtime_failure = "That's not right:\n"


def gen_case(*, sign=None, trailing_junk=None):
    if sign == "-":
        n = random.randint(-(2**31), -1)
    elif sign == "+":
        n = random.randint(0, 2**31 - 1)
    else:
        n = random.randint(-(2**31), 2**31 - 1)
    s = str(n)
    if trailing_junk is None:
        trailing_junk = random.random() < 0.8
    if trailing_junk:
        # Append a non-digit, then arbitrary trailing characters that atoi must ignore.
        s += random.choice(JUNK)
        s += "".join(random.choice(JUNK + "0123456789") for _ in range(random.randint(0, 5)))
    return s, n


def as_signed(v):
    return v - (1 << 64) if v >= (1 << 63) else v


def run_one(so_path, numstr, *, quiet):
    try:
        p = subprocess.run(
            ["/challenge/harness", so_path, numstr],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            f"atoi({numstr!r}) never returned --- it ran too long and was killed. "
            "If the loop doesn't advance the pointer (inc rdi) and stop at a non-digit, it spins forever."
        )
    if p.returncode != 0:
        stderr = p.stderr.decode("utf-8", errors="replace").strip()
        details = f"\n\nHarness stderr:\n{stderr}" if stderr else ""
        raise AssertionError(f"The harness exited abnormally (status {p.returncode}) on input {numstr!r}.{details}")
    if not quiet and p.stderr:
        sys.stderr.write(p.stderr.decode("utf-8", errors="replace"))
        sys.stderr.flush()
    if len(p.stdout) < 8:
        raise AssertionError("The harness never reported a result --- did your atoi crash?")
    return int.from_bytes(p.stdout[-8:], "little")


def diagnose(numstr, expected, got):
    g = as_signed(got)
    neg = numstr.startswith("-")
    body = numstr[1:] if neg else numstr
    # Value if the loop never stopped --- treating every byte as a digit (c - '0').
    over = 0
    for c in body:
        over = over * 10 + (ord(c) - ord("0"))
    over = -over if neg else over
    if not body.isdigit() and g == over:
        return " Your loop ran past the number into the trailing characters --- stop at the first byte that isn't a digit."
    # Sum of just the leading digits (the *10 was skipped).
    digits = ""
    for c in body:
        if not c.isdigit():
            break
        digits += c
    if digits:
        ds = sum(int(c) for c in digits)
        if g == (-ds if neg else ds):
            return " That's the sum of the digits --- multiply the running total by 10 as you go."
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f'/challenge/harness {so_path} <number-then-junk>')
    print("")
    forced = [("-", True), ("+", True), (None, False)]
    for i in range(ROUNDS):
        sign, trailing_junk = forced[i] if i < len(forced) else (None, None)
        numstr, expected = gen_case(sign=sign, trailing_junk=trailing_junk)
        got = run_one(so_path, numstr, quiet=(i != 0))
        assert got == (expected & MASK), (
            f"atoi({numstr!r}) should be {expected} (stop at the first non-digit), "
            f"but your atoi returned {as_signed(got)}."
            + diagnose(numstr, expected, got)
        )
        if i != 0:
            print(f"  ok: atoi({numstr!r}) = {as_signed(got)}")
    return True
