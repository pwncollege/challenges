import __main__ as checker
import random
import signal
import subprocess
import sys

shared = True
give_flag = True
solve_symbol = "solve"

check_disassembly_prologue = "Let's make sure your function uses unsigned division..."
check_disassembly_success = "Your function uses div. Now let's check its quotient and remainder!"
check_disassembly_failure = "The division instruction is missing:\n"

check_runtime_prologue = "Let's call solve() on two-digit values and check the digit sums..."
check_runtime_success = "Every value produced the right digit sum!"
check_runtime_failure = "That didn't come out right:\n"


def check_disassembly(disas):
    for insn in disas:
        if insn.mnemonic == "div":
            return True
        if insn.mnemonic == "ret":
            break
    raise AssertionError(
        "Use the unsigned `div` instruction to split the value into a quotient and remainder "
        "before your function returns."
    )


def run_one(so_path, value, *, quiet):
    try:
        p = subprocess.run(
            ["/challenge/harness", so_path, str(value)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            f"solve({value}) never returned --- it ran too long and was killed. "
            "A function has to reach a `ret`."
        )

    if p.returncode != 0:
        stderr = p.stderr.decode("utf-8", errors="replace").strip()
        details = f"\n\nHarness stderr:\n{stderr}" if stderr else ""
        if p.returncode == -signal.SIGFPE:
            details += (
                "\n\nThe CPU reported a division error. Before `div`, make sure the divisor "
                "is nonzero and the high half of the dividend in rdx is zero."
            )
        raise AssertionError(
            f"The harness exited abnormally (status {p.returncode}) on value {value}.{details}"
        )

    if not quiet and p.stderr:
        sys.stderr.write(p.stderr.decode("utf-8", errors="replace"))
        sys.stderr.flush()
    if len(p.stdout) < 8:
        raise AssertionError("The harness never reported a result --- did your solve crash?")
    return int.from_bytes(p.stdout[-8:], "little")


def diagnose(value, got):
    quotient, remainder = divmod(value, 10)
    if got == quotient:
        return " That is only the quotient; add the remainder too."
    if got == remainder:
        return " That is only the remainder; add the quotient too."
    return ""


def check_runtime(so_path):
    cases = [10, 42, 99] + [random.randint(10, 99) for _ in range(6)]

    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} {cases[0]}")
    print("")

    for i, value in enumerate(cases):
        got = run_one(so_path, value, quiet=(i != 0))
        quotient, remainder = divmod(value, 10)
        expected = quotient + remainder
        assert got == expected, (
            f"solve({value}) should return {quotient} + {remainder} = {expected}, "
            f"but returned {got}."
            + diagnose(value, got)
        )
        if i != 0:
            print(f"  ok: solve({value}) = {expected}")
    return True
