import __main__ as checker
import random
import subprocess

# A shared-library challenge: the learner submits `itoa` inside a .so. The flag
# is dispensed by this (root) checker after it verifies the string itoa wrote.
# The harness that runs the .so is unprivileged and never holds the flag.
shared = True
give_flag = True
solve_symbol = "itoa"


MASK = (1 << 64) - 1


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
            "If the divide loop doesn't shrink the value toward 0 each pass, it spins forever."
        )
    if p.returncode != 0:
        raise AssertionError(f"The harness exited abnormally (status {p.returncode}) on value {value}.")
    return p.stdout


check_runtime_prologue = "Let's hand your itoa positive and negative numbers and check the text it writes..."
check_runtime_success = "Every number printed correctly, sign and all!"
check_runtime_failure = "That text wasn't right:\n"


def diagnose(v, expected, got):
    if v < 0:
        if got == str(v & MASK).encode():
            return " div is unsigned, so a negative value became enormous --- peel the '-' off first, then convert the magnitude."
        if got.startswith(b"-") and len(got) == len(expected) - 1:
            return " You wrote the '-' but the returned length didn't count it --- add 1 to the length for the sign."
    if len(expected) > 1 and got == expected[::-1]:
        return " The digits came out reversed --- emit them most-significant first."
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <value>")
    print("")
    cases = [0, 1, -1, 7, -7, 42, -42, 100, -100, 12345, -12345, 2**31, -(2**31), 10**12]
    cases += [random.randint(-(2**63 - 1), 2**63 - 1) for _ in range(5)]
    for i, v in enumerate(cases):
        got = run_one(so_path, v, quiet=(i != 0))
        expected = str(v).encode()
        assert got == expected, f"itoa({v}, buf) should write {expected!r}, but it wrote {got!r}.{diagnose(v, expected, got)}"
        if i != 0:
            print(f"  ok: itoa({v}) wrote {got!r}")
    return True
