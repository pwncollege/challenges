import __main__ as checker
import random
import subprocess

shared = True
give_flag = True

check_runtime_prologue = (
    "Let's load your shared library and call solve(secret) "
    "with a few random secrets to see if you return secret + 1..."
)
check_runtime_success = "Your function returned the right value every time!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_runtime(so_path):
    for _ in range(3):
        secret = random.randrange(0, 2**63)
        expected = (secret + 1) % (2**64)

        driver = (
            "import ctypes\n"
            f"lib = ctypes.CDLL({so_path!r})\n"
            "lib.solve.argtypes = [ctypes.c_uint64]\n"
            "lib.solve.restype = ctypes.c_uint64\n"
            f"print(lib.solve({secret}))\n"
        )

        print("")
        checker.print_prompt()
        checker.slow_print(
            f"python3 -c 'lib = ctypes.CDLL({so_path!r}); "
            f"print(lib.solve({secret}))'"
        )

        result = subprocess.run(
            ["python3", "-I", "-c", driver],
            capture_output=True,
            timeout=5,
        )

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            raise AssertionError(
                f"Your function exited abnormally (return code {result.returncode}).\n"
                f"Stderr from the loader:\n{stderr}"
            )

        try:
            got = int(result.stdout.strip())
        except ValueError:
            raise AssertionError(
                f"Your function returned non-integer output: {result.stdout!r}"
            ) from None

        if got != expected:
            raise AssertionError(
                f"Your function returned {got} when called with secret {secret}.\n"
                f"Expected {expected} (= secret + 1).\n"
                "Make sure you put your return value in `rax` before `ret`."
            )
