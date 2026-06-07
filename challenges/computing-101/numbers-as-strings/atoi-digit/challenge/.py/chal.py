import __main__ as checker
import subprocess

# A shared-library challenge: the learner submits `atoi_digit` inside a .so, and
# the flag is dispensed by this (root) checker only after it independently
# verifies the value `atoi_digit` returned. The harness that actually runs the
# .so is unprivileged and never holds the flag.
shared = True
give_flag = True
solve_symbol = "atoi_digit"  # this level's entrypoint is named atoi_digit, not solve

check_runtime_prologue = "Let's hand your atoi_digit() each decimal digit, one at a time..."
check_runtime_success = "Every digit decoded correctly!"
check_runtime_failure = "That digit didn't decode right:\n"


def as_signed(v):
    return v - (1 << 64) if v >= (1 << 63) else v


def run_one(so_path, s, *, quiet):
    try:
        p = subprocess.run(
            ["/challenge/harness", so_path, s],
            stdout=subprocess.PIPE,
            stderr=(subprocess.DEVNULL if quiet else None),
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            f"atoi_digit({s!r}) never returned --- it ran too long and was killed. "
            "A function has to reach a `ret`; an accidental loop with no way out spins forever."
        )
    if p.returncode != 0:
        raise AssertionError(
            f"The harness exited abnormally (status {p.returncode}) on input {s!r}."
        )
    if len(p.stdout) < 8:
        raise AssertionError("The harness never reported a result --- did your atoi_digit crash?")
    return int.from_bytes(p.stdout[-8:], "little")


def diagnose(d, got):
    if got == ord(d):
        return f" That's the ASCII code of '{d}' --- subtract '0' (0x30) to turn the character into its value."
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <digit>")
    print("")
    for i, d in enumerate("0123456789"):
        got = run_one(so_path, d, quiet=(i != 0))
        assert got == int(d), (
            f"atoi_digit({d!r}) should be {d}, but your atoi_digit returned {as_signed(got)}."
            + diagnose(d, got)
        )
        if i != 0:
            print(f"  ok: atoi_digit({d!r}) = {got}")
    return True
