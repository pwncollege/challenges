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
            "If the divide loop doesn't shrink the value toward 0 each pass, it spins forever."
        )
    if p.returncode != 0:
        raise AssertionError(f"The harness exited abnormally (status {p.returncode}) on value {value}.")
    return p.stdout


check_runtime_prologue = "Let's hand your itoa numbers of every length and check the text it writes..."
check_runtime_success = "Every number printed correctly!"
check_runtime_failure = "That text wasn't right:\n"


def diagnose(expected, got):
    if expected == b"0" and got == b"":
        return " 0 is the special case: the divide-by-10 loop runs zero times for it, so write '0' explicitly."
    if len(expected) > 1 and got == expected[::-1]:
        return " The digits came out reversed --- emit them most-significant first (push them as you divide, then pop)."
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <value>")
    print("")
    cases = [0, 1, 7, 9, 10, 42, 99, 100, 1000, 12345, 2**31, 2**32, 10**12]
    cases += [random.randint(0, 2**63 - 1) for _ in range(5)]
    for i, v in enumerate(cases):
        got = run_one(so_path, v, quiet=(i != 0))
        expected = str(v).encode()
        assert got == expected, f"itoa({v}, buf) should write {expected!r}, but it wrote {got!r}.{diagnose(expected, got)}"
        if i != 0:
            print(f"  ok: itoa({v}) wrote {got!r}")
    return True
