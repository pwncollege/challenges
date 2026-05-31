import __main__ as checker
import subprocess

shared = True
give_flag = False

check_runtime_prologue = (
    "Let's load your shared library and call solve(flag, len) "
    "to see if you write the flag out to stdout..."
)
check_runtime_success = "If your solve is right, the flag is printed above!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_runtime(so_path):
    flag = checker.read_flag().rstrip(b"\n")

    driver = (
        "import ctypes\n"
        f"lib = ctypes.CDLL({so_path!r})\n"
        f"buf = ctypes.create_string_buffer({bytes(flag)!r}, {len(flag)})\n"
        "lib.solve.argtypes = [ctypes.c_void_p, ctypes.c_uint64]\n"
        "lib.solve.restype = None\n"
        f"lib.solve(ctypes.addressof(buf), {len(flag)})\n"
    )

    print("")
    checker.print_prompt()
    checker.slow_print(
        f"python3 -c 'lib = ctypes.CDLL({so_path!r}); "
        f"lib.solve(<flag buffer>, {len(flag)})'"
    )
    print("")

    subprocess.run(
        ["python3", "-I", "-c", driver],
        timeout=5,
    )
    print("")

    return True
