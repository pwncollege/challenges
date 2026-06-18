import __main__ as checker
import random
import subprocess

# Shared-library challenge: the learner submits `chr_lower` inside a .so. The flag is
# dispensed by this (root) checker only after it independently verifies the
# values chr_lower() returns. The harness that runs the .so is unprivileged and
# never holds the flag.
shared = True
give_flag = True
solve_symbol = "chr_lower"

SET = 0x20  # ASCII case bit

check_runtime_prologue = "Let's hand your chr_lower() uppercase letters and see if it lowercases them..."
check_runtime_success = "Every letter lowercased correctly!"
check_runtime_failure = "That didn't come out right:\n"


def as_signed(v):
    return v - (1 << 64) if v >= (1 << 63) else v


def run_one(so_path, x, *, quiet):
    try:
        p = subprocess.run(
            ["/challenge/harness", so_path, hex(x)],
            stdout=subprocess.PIPE,
            stderr=(subprocess.DEVNULL if quiet else None),
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            f"chr_lower({hex(x)}) never returned --- it ran too long and was killed. "
            "A function has to reach a `ret`."
        )
    if p.returncode != 0:
        raise AssertionError(f"The harness exited abnormally (status {p.returncode}) on chr_lower({hex(x)}).")
    if len(p.stdout) < 8:
        raise AssertionError("The harness never reported a result --- did your chr_lower crash?")
    return int.from_bytes(p.stdout[-8:], "little")


def diagnose(x, got):
    if got == x:
        return " That's the input unchanged --- turn the case bit on with `or rax, 0x20`."
    return ""


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <uppercase letter>")
    print("")
    cases = [ord(c) for c in "AZBMQ"]
    cases += [random.randrange(ord("A"), ord("Z") + 1) for _ in range(5)]
    for i, x in enumerate(cases):
        got = run_one(so_path, x, quiet=(i != 0))
        want = x | SET
        assert got == want, (
            f"chr_lower({chr(x)!r} == {hex(x)}) should be {hex(want)} ({chr(want)!r}), "
            f"but your chr_lower returned {hex(got)}." + diagnose(x, got)
        )
        if i != 0:
            print(f"  ok: chr_lower({chr(x)!r}) = {hex(got)} ({chr(want)!r})")
    return True
