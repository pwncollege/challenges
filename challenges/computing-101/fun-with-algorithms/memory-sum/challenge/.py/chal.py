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


def diagnose(total, got):
    if total == 0 and got == b"":
        return " A total of 0 printed nothing --- your itoa needs to handle 0 as a special case."
    if total < 0 and got == str(total & ((1 << 64) - 1)).encode():
        return " A negative total printed as a huge unsigned number --- your itoa has to handle the sign."
    if len(got) > 1 and got == str(total).encode()[::-1]:
        return " The digits came out reversed --- itoa must emit them most-significant first."
    return ""


def check_runtime(binary_path):
    checker.print_prompt()
    checker.slow_print(f"{binary_path} <num0> <num1> ...")
    print("")
    cases = [[], [0], [42], [-42], [3, -5, 10], [100, -200, 50], [10**6, -(10**6)]]
    cases += [gen_case() for _ in range(5)]
    for i, nums in enumerate(cases):
        total = sum(nums)
        try:
            p = subprocess.run(
                [binary_path] + [str(n) for n in nums],
                stdout=subprocess.PIPE,
                stderr=(subprocess.DEVNULL if i != 0 else None),
                timeout=5,
            )
        except subprocess.TimeoutExpired:
            raise AssertionError(
                f"Your program didn't finish on arguments {nums!r} --- an unterminated loop runs forever. "
                "Check that your argv walk stops at argc and that atoi/itoa each make progress."
            )
        if p.returncode < 0:
            signum = -p.returncode
            signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
            raise AssertionError(f"Your program crashed ({signame}) on arguments {nums!r}.")
        got = p.stdout
        expected = str(total).encode()
        assert got == expected, (
            f"on arguments {nums!r}, your program should print {expected!r}, but it printed {got!r}."
            + diagnose(total, got)
        )
        print(f"  ok: {nums!r} -> printed {got!r}")
    return True
