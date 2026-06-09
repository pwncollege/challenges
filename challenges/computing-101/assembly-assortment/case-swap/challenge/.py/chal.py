import __main__ as checker
import random
import signal
import subprocess
import sys

# Shared-library challenge: the learner submits `str_swapcase` inside a .so. The flag is
# dispensed by this (root) checker only after it independently verifies the bytes
# str_swapcase() writes back. The harness that runs the .so is unprivileged and never
# holds the flag.
shared = True
give_flag = True
solve_symbol = "str_swapcase"

CASE_BIT = 0x20  # toggling this bit swaps a letter's case

check_runtime_prologue = "Let's hand your str_swapcase() some mixed-case strings and read back what it writes..."
check_runtime_success = "Every letter's case flipped correctly --- your loop walked the whole string!"
check_runtime_failure = "That didn't come out right:\n"


def expected(data):
    # toggle the case of every letter by flipping the 0x20 bit
    return bytes(b ^ CASE_BIT for b in data)


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
            f"str_swapcase() never returned on {data!r} --- it ran too long and was killed. "
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
        return " That's the input unchanged --- flip the case bit on each letter with `xor` (the 0x20 bit)."
    want = expected(data)
    if len(got) == len(want) and got[:1] == want[:1] and got[1:] == data[1:]:
        return " Only the first letter changed --- you need a loop that advances to the next byte and repeats until the NUL."
    return ""


def random_letter():
    c = random.randrange(ord("A"), ord("Z") + 1)
    return c | CASE_BIT if random.getrandbits(1) else c  # pick upper or lower at random


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <hex bytes>")
    print("")

    cases = [
        b"a",        # a single lowercase letter -> uppercase
        b"A",        # a single uppercase letter -> lowercase
        b"HeLLo",    # already mixed
    ]
    for _ in range(8):
        n = random.randint(1, 40)
        cases.append(bytes(random_letter() for _ in range(n)))

    for i, data in enumerate(cases):
        got = run_one(so_path, data, quiet=(i != 0))
        want = expected(data)
        assert got == want, (
            f"str_swapcase({data!r}) should be {want!r}, but your str_swapcase produced {got!r}."
            + diagnose(data, got)
        )
        if i != 0:
            print(f"  ok: {data.decode()!r} -> {got.decode()!r}")
    return True
