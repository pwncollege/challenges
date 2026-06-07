import __main__ as checker
import random
import signal
import subprocess

# A full-program challenge: the learner assembles and links their own complete
# executable, and common/check runs it as-is (executable mode). We pass it
# several numbers as arguments and check that it PRINTS their sum to stdout. The
# flag is dispensed by this (root) checker after the run passes.
executable = True
give_flag = True

check_runtime_prologue = "Let's run your program on some lists of numbers and read the total it prints..."
check_runtime_success = "Every total printed correctly!"
check_runtime_failure = "That total wasn't right:\n"


def gen_case():
    k = random.randint(1, 6)
    return [random.randint(-(10**6), 10**6) for _ in range(k)]


def check_runtime(binary_path):
    checker.print_prompt()
    checker.slow_print(f"{binary_path} <num0> <num1> ...")
    print("")
    cases = [[], [0], [42], [-42], [3, -5, 10], [100, -200, 50], [10**6, -(10**6)]]
    cases += [gen_case() for _ in range(5)]
    for i, nums in enumerate(cases):
        total = sum(nums)
        p = subprocess.run(
            [binary_path] + [str(n) for n in nums],
            stdout=subprocess.PIPE,
            stderr=(subprocess.DEVNULL if i != 0 else None),
            timeout=5,
        )
        if p.returncode < 0:
            signum = -p.returncode
            signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
            raise AssertionError(f"Your program crashed ({signame}) on arguments {nums!r}.")
        got = p.stdout
        expected = str(total).encode()
        assert got == expected, (
            f"on arguments {nums!r}, your program should print {expected!r}, but it printed {got!r}."
        )
        print(f"  ok: {nums!r} -> printed {got!r}")
    return True
