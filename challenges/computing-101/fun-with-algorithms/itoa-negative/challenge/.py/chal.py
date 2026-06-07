import __main__ as checker
import random
import subprocess

# A shared-library challenge: the learner submits `itoa` inside a .so. The flag
# is dispensed by this (root) checker after it verifies the string itoa wrote.
# The harness that runs the .so is unprivileged and never holds the flag.
shared = True
give_flag = True
solve_symbol = "itoa"


def run_one(so_path, value, *, quiet):
    p = subprocess.run(
        ["/challenge/harness", so_path, str(value)],
        stdout=subprocess.PIPE,
        stderr=(subprocess.DEVNULL if quiet else None),
        timeout=5,
    )
    if p.returncode != 0:
        raise AssertionError(f"The harness exited abnormally (status {p.returncode}) on value {value}.")
    return p.stdout


check_runtime_prologue = "Let's hand your itoa positive and negative numbers and check the text it writes..."
check_runtime_success = "Every number printed correctly, sign and all!"
check_runtime_failure = "That text wasn't right:\n"


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <value>")
    print("")
    cases = [0, 1, -1, 7, -7, 42, -42, 100, -100, 12345, -12345, 2**31, -(2**31), 10**12]
    cases += [random.randint(-(2**63 - 1), 2**63 - 1) for _ in range(5)]
    for i, v in enumerate(cases):
        got = run_one(so_path, v, quiet=(i != 0))
        expected = str(v).encode()
        assert got == expected, f"itoa({v}, buf) should write {expected!r}, but it wrote {got!r}."
        if i != 0:
            print(f"  ok: itoa({v}) wrote {got!r}")
    return True
