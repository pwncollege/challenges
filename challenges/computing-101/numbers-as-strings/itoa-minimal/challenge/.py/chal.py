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
            stderr=subprocess.PIPE,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            f"itoa({value}, buf) never returned --- it ran too long and was killed. "
            "A function has to reach a `ret`; an accidental loop with no way out spins forever."
        )
    if p.returncode != 0:
        stderr = p.stderr.decode("utf-8", errors="replace").strip()
        details = f"\n\nHarness stderr:\n{stderr}" if stderr else ""
        raise AssertionError(f"The harness exited abnormally (status {p.returncode}) on value {value}.{details}")
    return p.stdout


check_runtime_prologue = "Let's hand your itoa each number 0-99 and check it writes no extra digit..."
check_runtime_success = "Every number came out at exactly the right length!"
check_runtime_failure = "That text wasn't right:\n"


def diagnose(v, expected, got):
    if v == 0 and got != b"0":
        return " 0 is the special case --- dividing it by 10 gives a quotient of 0 right away, so write a single '0' explicitly."
    if v < 10 and got == b"0" + expected:
        return " A single-digit number shouldn't be zero-padded --- only write the tens digit when the quotient is non-zero."
    if len(expected) == 2 and got == expected[::-1]:
        return " The two digits are swapped --- tens first, then ones."
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <value>")
    print("")
    # Single digits (quotient 0 -> one char), two-digit numbers, and the 0 case.
    cases = [0, 7, 9, 10, 42, 99] + [random.randint(0, 9) for _ in range(2)] + [random.randint(10, 99) for _ in range(3)]
    for i, v in enumerate(cases):
        got = run_one(so_path, v, quiet=(i != 0))
        expected = str(v).encode()  # minimal --- no leading zeros
        assert got == expected, f"itoa({v}, buf) should write {expected!r}, but it wrote {got!r}.{diagnose(v, expected, got)}"
        if i != 0:
            print(f"  ok: itoa({v}) wrote {got!r}")
    return True
