import __main__ as checker
import random
import subprocess

# A shared-library challenge exporting TWO functions, atoi_digit and atoi. The
# flag is dispensed by this (root) checker only after it independently verifies
# both. The harness that runs the .so is unprivileged and never holds the flag.
shared = True
give_flag = True
solve_symbol = "atoi"  # common/check validates `atoi`; the harness also checks atoi_digit


def as_signed(v):
    return v - (1 << 64) if v >= (1 << 63) else v


def run_one(so_path, fname, s, *, quiet):
    try:
        p = subprocess.run(
            ["/challenge/harness", so_path, fname, s],
            stdout=subprocess.PIPE,
            stderr=(subprocess.DEVNULL if quiet else None),
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            f"{fname}({s!r}) never returned --- it ran too long and was killed. "
            "Every path has to reach a `ret`; an accidental loop with no way out spins forever."
        )
    if p.returncode != 0:
        raise AssertionError(
            f"The harness exited abnormally (status {p.returncode}) on {fname}({s!r})."
        )
    if len(p.stdout) < 8:
        raise AssertionError("The harness never reported a result --- did your code crash?")
    return int.from_bytes(p.stdout[-8:], "little")


check_runtime_prologue = "Let's test your atoi_digit on single digits, then your atoi on two-digit numbers..."
check_runtime_success = "Both functions check out!"
check_runtime_failure = "That's not right:\n"


def diagnose(s, got):
    a, b = int(s[0]), int(s[1])
    g = as_signed(got)
    if g == a + b:
        return " That's first + second --- the tens digit has to be multiplied by 10 before you add the ones."
    if g == b and a != 0:
        return " That's only the ones digit --- the tens digit got lost along the way."
    if g == a and b != 0:
        return " That's only the tens digit --- did you forget to add the ones?"
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} atoi_digit <digit>   # then: atoi <two-digit number>")
    print("")

    # Phase 1: atoi_digit still works on every single digit (last level's contract).
    for i, d in enumerate("0123456789"):
        got = run_one(so_path, "atoi_digit", d, quiet=(i != 0))
        ascii_hint = f" That's the ASCII code of '{d}' --- subtract '0'." if got == ord(d) else ""
        assert got == int(d), f"atoi_digit({d!r}) should be {d}, but it returned {as_signed(got)}.{ascii_hint}"
        if i != 0:
            print(f"  ok: atoi_digit({d!r}) = {got}")

    # Phase 2: atoi on two-character numbers (place value: first*10 + second).
    cases = [f"{n:02d}" for n in (0, 7, 10, 42, 99)]
    cases += [f"{random.randint(0, 99):02d}" for _ in range(5)]
    for j, s in enumerate(cases):
        got = run_one(so_path, "atoi", s, quiet=(j != 0))
        assert got == int(s), f"atoi({s!r}) should be {int(s)}, but it returned {as_signed(got)}.{diagnose(s, got)}"
        if j != 0:
            print(f"  ok: atoi({s!r}) = {got}")
    return True
