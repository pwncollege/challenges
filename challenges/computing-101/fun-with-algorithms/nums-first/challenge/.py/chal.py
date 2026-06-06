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

check_runtime_prologue = "Let's hand your solve() a few arrays of numbers..."
check_runtime_success = "You picked out the first number every time!"
check_runtime_failure = "That wasn't the right value:\n"


def gen_case():
    count = random.randint(1, 6)
    nums = [random.randint(-(2**31), 2**31 - 1) for _ in range(count)]
    return nums, nums[0]  # this level: return the first number


def as_signed(v):
    return v - (1 << 64) if v >= (1 << 63) else v


def run_one(so_path, nums, *, quiet):
    argv = ["/challenge/harness", so_path] + [str(n) for n in nums]
    p = subprocess.run(
        argv,
        stdout=subprocess.PIPE,
        stderr=(subprocess.DEVNULL if quiet else None),
        timeout=5,
    )
    if p.returncode != 0:
        raise AssertionError(
            f"The harness exited abnormally (status {p.returncode}) on input {nums!r}."
        )
    if len(p.stdout) < 8:
        raise AssertionError("The harness never reported a result --- did your solve crash?")
    return int.from_bytes(p.stdout[-8:], "little")


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f'/challenge/harness {so_path} <num0> <num1> ...')
    print("")
    for i in range(ROUNDS):
        nums, expected = gen_case()
        got = run_one(so_path, nums, quiet=(i != 0))
        assert got == (expected & MASK), (
            f"solve({nums!r}) should return nums[0] = {expected}, "
            f"but your solve returned {as_signed(got)}."
        )
        if i != 0:
            print(f"  ok: solve({nums!r}) = {as_signed(got)}")
    return True
