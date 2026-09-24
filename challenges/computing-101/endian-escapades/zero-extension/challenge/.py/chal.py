import __main__ as checker
import random
import subprocess

shared = True
give_flag = True
solve_symbol = "solve"

check_runtime_prologue = "Let's call your solve() on unsigned bytes and check the 64-bit results..."
check_runtime_success = "Every byte zero-extended correctly!"
check_runtime_failure = "That didn't come out right:\n"

MASK64 = (1 << 64) - 1


def signed_byte(value):
    return value - 0x100 if value & 0x80 else value


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
    sign_extended = signed_byte(value) & MASK64
    if value & 0x80 and got == sign_extended:
        return " That is sign extension; this byte is unsigned, so the new high bits must be zero."
    if (got & 0xFF) == value:
        return " The low byte is right, but the high bits were not cleared."
    return ""


def check_runtime(so_path):
    cases = [0x00, 0x01, 0x7F, 0x80, 0x81, 0xFF]
    cases += [random.randrange(0x100) for _ in range(6)]

    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} 0x{cases[0]:02x}")
    print("")

    for i, value in enumerate(cases):
        got = run_one(so_path, value, quiet=(i != 0))
        assert got == value, (
            f"solve(pointer to byte {hex(value)}) should return {value} ({hex(value)}), "
            f"but returned {got} ({hex(got)})."
            + diagnose(value, got)
        )
        if i != 0:
            print(f"  ok: byte {hex(value)} -> {value}")
    return True
