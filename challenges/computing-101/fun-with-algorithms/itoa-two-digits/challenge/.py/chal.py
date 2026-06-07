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
    try:
        p = subprocess.run(
            ["/challenge/harness", so_path, str(value)],
            stdout=subprocess.PIPE,
            stderr=(subprocess.DEVNULL if quiet else None),
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            f"itoa({value}, buf) never returned --- it ran too long and was killed. "
            "A function has to reach a `ret`; an accidental loop with no way out spins forever."
        )
    if p.returncode != 0:
        raise AssertionError(f"The harness exited abnormally (status {p.returncode}) on value {value}.")
    return p.stdout


check_runtime_prologue = "Let's hand your itoa some two-digit numbers and check the text it writes..."
check_runtime_success = "Every number came out as the right two digits!"
check_runtime_failure = "That text wasn't right:\n"


def diagnose(expected, got):
    if got == expected[::-1]:
        return " The two digits are swapped --- write the tens digit to buf[0] and the ones to buf[1]."
    if len(got) == 2 and got[0] < 10 and got[1] < 10:
        return " Those are raw digit values, not characters --- add '0' to each before storing it."
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <value>")
    print("")
    cases = list(range(0, 10)) + [10, 42, 99] + [random.randint(0, 99) for _ in range(5)]
    for i, v in enumerate(cases):
        got = run_one(so_path, v, quiet=(i != 0))
        expected = f"{v:02d}".encode()  # exactly two digits, zero-padded
        assert got == expected, f"itoa({v}, buf) should write {expected!r}, but it wrote {got!r}.{diagnose(expected, got)}"
        if i != 0:
            print(f"  ok: itoa({v}) wrote {got!r}")
    return True
