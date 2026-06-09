import __main__ as checker
import random
import signal
import subprocess
import sys

# Shared-library challenge: the learner submits `str_upper` inside a .so. The flag is
# dispensed by this (root) checker only after it independently verifies the bytes
# str_upper() writes back. The harness that runs the .so is unprivileged and never
# holds the flag.
shared = True
give_flag = True
solve_symbol = "str_upper"

CLEAR_MASK = 0xDF  # ~0x20: every bit kept except the ASCII case bit

check_runtime_prologue = "Let's hand your str_upper() some lowercase strings and read back what it writes..."
check_runtime_success = "Every letter uppercased correctly --- your loop walked the whole string!"
check_runtime_failure = "That didn't come out right:\n"


def expected(data):
    # uppercase every byte by clearing the 0x20 bit
    return bytes(b & CLEAR_MASK for b in data)


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
            f"str_upper() never returned on {data!r} --- it ran too long and was killed. "
            "A loop over a string needs a way out: stop when you reach the NUL byte, "
            "and the function has to reach a `ret`."
        )
    if p.returncode < 0:
        signum = -p.returncode
        signame = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"signal {signum}"
        sys.stderr.write(("Segmentation fault" if signum == signal.SIGSEGV else signame) + "\n")
        sys.stderr.flush()
        raise AssertionError(
            f"The harness crashed with {signame} on {data!r}. "
            "Are you reading and writing one byte at a time (a byte register like `cl`, "
            "or a `byte ptr` access), and advancing your pointer each step?"
        )
    if p.returncode != 0:
        raise AssertionError(f"The harness exited abnormally (status {p.returncode}) on {data!r}.")
    return p.stdout


def diagnose(data, got):
    if got == data:
        return " That's the input unchanged --- clear the case bit on each letter with `and` (the mask 0xDF keeps every bit except 0x20)."
    want = expected(data)
    if len(got) == len(want) and got[:1] == want[:1] and got[1:] == data[1:]:
        return " Only the first letter changed --- you need a loop that advances to the next byte and repeats until the NUL."
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <hex bytes>")
    print("")

    cases = [
        b"a",        # a single letter
        b"hello",    # a short word
        b"abcxyz",   # spans the alphabet
    ]
    for _ in range(8):
        n = random.randint(1, 40)
        cases.append(bytes(random.randrange(ord("a"), ord("z") + 1) for _ in range(n)))

    for i, data in enumerate(cases):
        got = run_one(so_path, data, quiet=(i != 0))
        want = expected(data)
        assert got == want, (
            f"str_upper({data!r}) should be {want!r}, but your str_upper produced {got!r}."
            + diagnose(data, got)
        )
        if i != 0:
            print(f"  ok: {data.decode()!r} -> {got.decode()!r}")
    return True
