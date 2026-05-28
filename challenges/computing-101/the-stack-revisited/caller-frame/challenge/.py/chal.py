import __main__ as checker
import subprocess

shared = True
give_flag = True

check_runtime_prologue = (
    "Let's see if your solve reads the secret out of the caller's frame..."
)
check_runtime_success = "Your function correctly read the caller's secret every time!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_runtime(so_path):
    for _ in range(3):
        print("")
        checker.print_prompt()
        checker.slow_print(f"/challenge/harness {so_path}")

        result = subprocess.run(
            ["/challenge/harness", so_path],
            capture_output=True,
            timeout=5,
        )

        stdout = result.stdout.decode("utf-8", errors="replace").strip()
        stderr = result.stderr.decode("utf-8", errors="replace").strip()

        if result.returncode != 0 and not stdout.startswith("WRONG"):
            raise AssertionError(
                f"The harness exited abnormally (return code {result.returncode}).\n"
                f"Stdout: {stdout}\nStderr: {stderr}"
            )

        if not stdout.startswith("OK "):
            raise AssertionError(
                f"Your function returned the wrong value.\n"
                f"Harness output: {stdout}\n"
                "The secret is stored at [rsp + 0x40] from your function's perspective."
            )
