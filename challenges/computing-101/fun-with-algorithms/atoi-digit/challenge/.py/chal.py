import __main__ as checker
import subprocess

# A shared-library challenge: the learner submits `solve` inside a .so, and the
# flag is dispensed by this (root) checker only after it independently verifies
# the value `solve` returned. The harness that actually runs the .so is
# unprivileged and never holds the flag.
shared = True
give_flag = True
solve_symbol = "atoi_digit"  # this level's entrypoint is named atoi_digit, not solve

check_runtime_prologue = "Let's hand your atoi_digit() each decimal digit, one at a time..."
check_runtime_success = "Every digit decoded correctly!"
check_runtime_failure = "That digit didn't decode right:\n"


def as_signed(v):
    return v - (1 << 64) if v >= (1 << 63) else v


def run_one(so_path, s, *, quiet):
    p = subprocess.run(
        ["/challenge/harness", so_path, s],
        stdout=subprocess.PIPE,
        stderr=(subprocess.DEVNULL if quiet else None),
        timeout=5,
    )
    if p.returncode != 0:
        raise AssertionError(
            f"The harness exited abnormally (status {p.returncode}) on input {s!r}."
        )
    if len(p.stdout) < 8:
        raise AssertionError("The harness never reported a result --- did your solve crash?")
    return int.from_bytes(p.stdout[-8:], "little")


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <digit>")
    print("")
    for i, d in enumerate("0123456789"):
        got = run_one(so_path, d, quiet=(i != 0))
        assert got == int(d), (
            f"atoi_digit({d!r}) should be {d}, but your solve returned {as_signed(got)}."
        )
        if i != 0:
            print(f"  ok: solve({d!r}) = {got}")
    return True
