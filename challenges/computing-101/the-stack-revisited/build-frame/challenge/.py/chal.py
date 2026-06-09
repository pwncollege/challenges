import __main__ as checker
import random
import signal
import subprocess
import sys

# Shared-library challenge: the learner submits `solve` inside a .so. The flag is
# dispensed by this (root) checker only after it independently verifies the
# value solve() returns. The harness that runs the .so is unprivileged and
# never holds the flag.
shared = True
give_flag = True
solve_symbol = "solve"

check_runtime_prologue = "Let's hand your solve() some byte strings and count the distinct values it finds..."
check_runtime_success = "Every count was right --- your frame held up!"
check_runtime_failure = "That didn't come out right:\n"


def as_signed(v):
    return v - (1 << 64) if v >= (1 << 63) else v


def run_one(so_path, data, *, quiet):
    hexbytes = data.hex()
    try:
        p = subprocess.run(
            ["/challenge/harness", so_path, hexbytes],
            stdout=subprocess.PIPE,
            stderr=(subprocess.DEVNULL if quiet else None),
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            f"solve() never returned on {data!r} --- it ran too long and was killed. "
            "Every loop needs a way out, and the function has to reach a `ret`."
        )
    if p.returncode < 0:
        signum = -p.returncode
        signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
        sys.stderr.write(("Segmentation fault" if signum == signal.SIGSEGV else signame) + "\n")
        sys.stderr.flush()
        raise AssertionError(
            f"The harness crashed with {signame} on {data!r}. "
            "If you made room with `sub rsp`, you must put the stack back the way you "
            "found it before `ret` (`mov rsp, rbp; pop rbp`), or the `ret` jumps to the wrong place."
        )
    if p.returncode != 0:
        raise AssertionError(f"The harness exited abnormally (status {p.returncode}) on {data!r}.")
    if len(p.stdout) < 8:
        raise AssertionError("The harness never reported a result --- did your solve crash?")
    return int.from_bytes(p.stdout[-8:], "little")


def diagnose(data, got):
    n = len(data)
    if got == n and n != len(set(data)):
        return " That's the total number of bytes --- you're counting every byte, not the distinct values."
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <hex bytes>")
    print("")

    cases = [
        bytes([0x41]),                                  # one byte -> 1 distinct
        bytes([0x41, 0x41, 0x41, 0x41]),                # all the same -> 1 distinct
        bytes([0x01, 0x02, 0x03, 0x04, 0x05]),          # all different -> 5 distinct
        bytes([0x41, 0x42, 0x41, 0x43, 0x42, 0x41]),    # repeats -> 3 distinct
        bytes(range(256)),                              # every value -> 256 distinct
    ]
    for _ in range(5):
        n = random.randint(1, 40)
        cases.append(bytes(random.randrange(256) for _ in range(n)))

    for i, data in enumerate(cases):
        got = run_one(so_path, data, quiet=(i != 0))
        want = len(set(data))
        assert got == want, (
            f"solve() on {len(data)} bytes should be {want} distinct, "
            f"but your solve returned {as_signed(got)}." + diagnose(data, got)
        )
        if i != 0:
            print(f"  ok: {len(data)} bytes -> {got} distinct")
    return True
