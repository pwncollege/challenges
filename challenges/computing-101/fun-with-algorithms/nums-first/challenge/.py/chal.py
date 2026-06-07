import __main__ as checker
import random
import signal
import subprocess

# A full-program challenge: the learner assembles and links their own complete
# executable, and common/check runs it *as-is* (executable mode --- no rebuild).
# We run it with a number as its only argument and check that it exits with that
# number's value. The flag is dispensed by this (root) checker after the run passes.
executable = True
give_flag = True

check_runtime_prologue = "Let's run your program on a few numbers and check its exit code..."
check_runtime_success = "Every number came back as the right exit code!"
check_runtime_failure = "That didn't come back right:\n"


def check_runtime(binary_path):
    checker.print_prompt()
    checker.slow_print(f"{binary_path} <number>; echo $?")
    print("")
    # Exit codes are one byte, so we stay in 0-255 (the range the DESCRIPTION promises).
    nums = [0, 1, 9, 42, 200, 255] + [random.randint(0, 255) for _ in range(4)]
    for i, n in enumerate(nums):
        try:
            p = subprocess.run(
                [binary_path, str(n)],
                stdout=subprocess.DEVNULL,
                stderr=(subprocess.DEVNULL if i != 0 else None),
                timeout=5,
            )
        except subprocess.TimeoutExpired:
            raise AssertionError(
                f"Your program didn't finish on the argument {n!r} --- an unterminated loop runs forever. "
                "Make sure it advances the pointer (inc rdi) and stops at the string's NUL."
            )
        rc = p.returncode
        if rc < 0:
            signum = -rc
            signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
            raise AssertionError(f"Your program crashed ({signame}) on the argument {n!r}.")
        hint = ""
        if rc == 0 and n != 0:
            hint = (" Exit code 0 --- read the number from argv[1] at [rsp+16] (argv[0] is the program name),"
                    " and move your result into rdi before the exit syscall.")
        elif n >= 10 and rc == sum(int(c) for c in str(n)):
            hint = " That's the sum of the digits --- multiply the running total by 10 as you go."
        assert rc == n, (
            f"on the argument {n!r}, your program should exit with code {n}, but it exited with {rc}.{hint}"
        )
        print(f"  ok: argument {n!r} -> exit code {rc}")
    return True
