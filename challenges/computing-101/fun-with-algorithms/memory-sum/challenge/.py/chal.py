import __main__ as checker
import random
import signal
import subprocess

# A full-program challenge: the learner assembles and links their own complete
# executable, and common/check runs it as-is (executable mode --- no rebuild).
# We pass it several numbers as arguments and check that it exits with their sum.
# The flag is dispensed by this (root) checker after the run passes.
executable = True
give_flag = True

check_runtime_prologue = "Let's run your program on some lists of numbers and check the total it exits with..."
check_runtime_success = "Every sum came back as the right exit code!"
check_runtime_failure = "That sum wasn't right:\n"


def gen_case():
    # Several numbers whose total stays in a byte (0-255), since the program
    # reports the sum as its exit code.
    k = random.randint(1, 5)
    return [random.randint(0, 255 // k) for _ in range(k)]


def check_runtime(binary_path):
    checker.print_prompt()
    checker.slow_print(f"{binary_path} <num0> <num1> ...; echo $?")
    print("")
    cases = [[], [0], [255], [1, 2, 3], [100, 100, 55]]  # edges: no args, one, full byte
    cases += [gen_case() for _ in range(5)]
    for nums in cases:
        total = sum(nums)
        p = subprocess.run(
            [binary_path] + [str(n) for n in nums],
            stdout=subprocess.DEVNULL,
            timeout=5,
        )
        rc = p.returncode
        if rc < 0:
            signum = -rc
            signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
            raise AssertionError(f"Your program crashed ({signame}) on arguments {nums!r}.")
        assert rc == total, (
            f"on arguments {nums!r}, your program should exit with {total}, but it exited with {rc}."
        )
        print(f"  ok: {nums!r} -> exit code {rc}")
    return True
