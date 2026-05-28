import __main__ as checker
import secrets
import subprocess

shared = True
give_flag = True

check_runtime_prologue = (
    "Let's load your shared library and call solve(callback). "
    "The callback stashes a token, and we'll check that it ran..."
)
check_runtime_success = "Your function called the callback correctly!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_runtime(so_path):
    token = secrets.token_hex(16)

    print("")
    checker.print_prompt()
    checker.slow_print(f"/challenge/harness {so_path} {token}")

    result = subprocess.run(
        ["/challenge/harness", so_path, token],
        capture_output=True,
        timeout=5,
    )

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise AssertionError(
            f"The harness exited abnormally (return code {result.returncode}).\n"
            f"Stderr:\n{stderr}"
        )

    if result.stdout.decode("utf-8", errors="replace") != token:
        raise AssertionError(
            f"The callback's token did not appear on stdout.\n"
            f"Expected: {token!r}\n"
            f"Got:      {result.stdout!r}\n"
            "Make sure your function calls the function pointer in rdi."
        )
