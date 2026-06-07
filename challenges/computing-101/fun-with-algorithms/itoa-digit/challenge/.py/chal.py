import __main__ as checker
import subprocess

# A shared-library challenge: the learner submits `itoa_digit` inside a .so. The
# flag is dispensed by this (root) checker after it verifies the returned char.
# The harness that runs the .so is unprivileged and never holds the flag.
shared = True
give_flag = True
solve_symbol = "itoa_digit"  # this level's entrypoint is named itoa_digit


def run_one(so_path, value, *, quiet):
    p = subprocess.run(
        ["/challenge/harness", so_path, str(value)],
        stdout=subprocess.PIPE,
        stderr=(subprocess.DEVNULL if quiet else None),
        timeout=5,
    )
    if p.returncode != 0:
        raise AssertionError(f"The harness exited abnormally (status {p.returncode}) on value {value}.")
    if len(p.stdout) < 8:
        raise AssertionError("The harness never reported a result --- did your itoa_digit crash?")
    return int.from_bytes(p.stdout[-8:], "little")


check_runtime_prologue = "Let's hand your itoa_digit each value 0-9 and check the character it returns..."
check_runtime_success = "Every digit turned into the right character!"
check_runtime_failure = "That character wasn't right:\n"


def check_runtime(so_path):
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} <value>")
    print("")
    for i, d in enumerate(range(10)):
        got = run_one(so_path, d, quiet=(i != 0))
        expected = ord("0") + d  # the ASCII character for that digit
        assert got == expected, (
            f"itoa_digit({d}) should return '{d}' ({expected} = {hex(expected)}), "
            f"but it returned {got} ({hex(got)})."
        )
        if i != 0:
            ch = chr(got) if 0x20 <= got < 0x7f else "?"
            print(f"  ok: itoa_digit({d}) = {got} ('{ch}')")
    return True
