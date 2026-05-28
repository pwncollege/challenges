import __main__ as checker
import random
import subprocess

shared = True
give_flag = True

check_runtime_prologue = (
    "Let's load your shared library and call solve(buf, len) "
    "with a random buffer..."
)
check_runtime_success = "Your function wrote the buffer correctly! Great job!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_runtime(so_path):
    test_bytes = bytes(random.randint(33, 126) for _ in range(32))

    driver = (
        "import ctypes\n"
        f"lib = ctypes.CDLL({so_path!r})\n"
        f"buf = ctypes.create_string_buffer({bytes(test_bytes)!r}, {len(test_bytes)})\n"
        "lib.solve.argtypes = [ctypes.c_void_p, ctypes.c_uint64]\n"
        "lib.solve.restype = None\n"
        f"lib.solve(ctypes.addressof(buf), {len(test_bytes)})\n"
    )

    print("")
    checker.print_prompt()
    checker.slow_print(
        f"python3 -c 'lib = ctypes.CDLL({so_path!r}); "
        f"lib.solve(buf, {len(test_bytes)})'"
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

    if result.stdout != test_bytes:
        raise AssertionError(
            f"Your function wrote {result.stdout!r} to stdout,\n"
            f"but we passed it a {len(test_bytes)}-byte buffer containing:\n"
            f"{test_bytes!r}\n"
            "Make sure you write exactly `rsi` bytes starting at `rdi` to fd 1."
        )
