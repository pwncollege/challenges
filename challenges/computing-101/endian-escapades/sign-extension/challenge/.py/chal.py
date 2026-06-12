import __main__ as checker
import random
import subprocess

shared = True
give_flag = True
solve_symbol = "solve"

check_runtime_prologue = "Let's call your solve() on signed bytes and check the 64-bit results..."
check_runtime_success = "Every byte sign-extended correctly!"
check_runtime_failure = "That didn't come out right:\n"

MASK64 = (1 << 64) - 1


def signed_byte(value):
    return value - 0x100 if value & 0x80 else value


def signed_u64(value):
    return value - (1 << 64) if value & (1 << 63) else value


def run_one(so_path, value, *, quiet):
    try:
        p = subprocess.run(
            ["/challenge/harness", so_path, hex(value)],
            stdout=subprocess.PIPE,
            stderr=(subprocess.DEVNULL if quiet else None),
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            f"solve(pointer to byte {hex(value)}) never returned --- it ran too long and was killed. "
            "A function has to reach a `ret`."
        )
    if p.returncode != 0:
        raise AssertionError(
            f"The harness exited abnormally (status {p.returncode}) on byte {hex(value)}."
        )
    if len(p.stdout) < 8:
        raise AssertionError("The harness never reported a result --- did your solve crash?")
    return int.from_bytes(p.stdout[-8:], "little")


def diagnose(value, got):
    if value & 0x80 and got == value:
        return " That is zero-extension: the low byte is right, but the high bytes are zero."
    if value & 0x80 and (got & 0xff) == value:
        return " The low byte is right, but the sign bit did not fill the high bytes."
    return ""


def check_runtime(so_path):
    cases = [0x00, 0x01, 0x7F, 0x80, 0x81, 0xFF]
    cases += [random.randrange(0x00, 0x80) for _ in range(3)]
    cases += [random.randrange(0x80, 0x100) for _ in range(3)]

    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} 0x{cases[0]:02x}")
    print("")

    for i, value in enumerate(cases):
        got = run_one(so_path, value, quiet=(i != 0))
        want_signed = signed_byte(value)
        want = want_signed & MASK64
        assert got == want, (
            f"solve(pointer to byte {hex(value)}) should return {want_signed} "
            f"({hex(want)} as 64 bits), but returned {signed_u64(got)} ({hex(got)})."
            + diagnose(value, got)
        )
        if i != 0:
            print(f"  ok: byte {hex(value)} -> {signed_byte(value)}")
    return True
