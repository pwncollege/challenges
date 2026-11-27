import __main__ as checker
import os
import random
import select
import signal
import subprocess

executable = True
give_flag = True
check_runtime_prologue = "Let's try your calculator with positive, negative, and zero results..."
check_runtime_success = "Your scanner, arithmetic, and formatter work together!"
check_runtime_failure = "The calculation needs another look:\n"


def run_one(filename, expression):
    with subprocess.Popen(
        [filename], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, start_new_session=True,
    ) as process:
        try:
            prompt = b""
            while len(prompt) < len(b"calc> "):
                ready, _, _ = select.select([process.stdout], [], [], 3)
                assert ready, "No complete prompt appeared before input. Print 'calc> ' before reading."
                chunk = os.read(process.stdout.fileno(), len(b"calc> ") - len(prompt))
                assert chunk, f"Your program ended before its prompt was complete: {prompt!r}."
                prompt += chunk
            assert prompt == b"calc> ", f"Expected the prompt b'calc> ', got {prompt!r}."
            output, errors = process.communicate(expression.encode(), timeout=3)
        except subprocess.TimeoutExpired:
            raise AssertionError(
                f"Your program did not finish for {expression!r}. "
                "This calculator reads one expression, prints one result, and exits."
            )
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    assert process.returncode == 0, (
        f"Your calculator exited with status {process.returncode} for {expression!r}.\n"
        + errors.decode(errors="replace")
    )
    return output


def check_runtime(filename):
    cases = [(12, "+", 34), (12, "-", 34), (12, "*", -3), (0, "+", 0),
             (-7, "-", -9), (-10000, "*", 10000), (42, "*", 0)]
    for operator in ["+", "-", "*"]:
        cases.append((random.randint(-10000, 10000), operator, random.randint(-10000, 10000)))
    for i, (left, operator, right) in enumerate(cases):
        expression = f"{left} {operator} {right}\n"
        if i == 4:
            expression = f"\t{left}\t{operator}  {right}\n"
        result = {"+": left + right, "-": left - right, "*": left * right}[operator]
        expected = f"{result}\n".encode()
        output = run_one(filename, expression)
        assert output == expected, (
            f"For {expression!r}, expected {expected!r} after the prompt, got {output!r}. "
            "Use the operator between the two operands and print the signed decimal result with a newline."
        )
        print(f"  ok: {expression.rstrip()!r} -> {result}")
    return True
