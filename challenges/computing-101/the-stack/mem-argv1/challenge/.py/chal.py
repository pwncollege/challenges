import __main__ as checker
import random
import string

give_flag = True
num_instructions = 4

check_disassembly_prologue = "Checking that your assembly reads from the argv[1] pointer on the stack..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's run your program with different arguments to check that it reads argv[1] from the stack!"
check_runtime_success = "Neat! Your program correctly exits with the first byte of argv[1] every time! Great job!"
check_runtime_failure = "Hmm, that's not right:\n"

def check_disassembly(disas):
    mov_operands = [d.op_str.split(", ") for d in disas if d.mnemonic == 'mov']

    has_argv1_deref = any(
        "[rsp + 0x10]" in src
        for _, src in mov_operands
    )
    assert has_argv1_deref, (
        "You need to dereference rsp with an offset of 16 bytes (using [rsp+16] or [rsp+0x10])\n"
        "to read the argv[1] pointer stored on the stack!\n"
        "Remember: [rsp] is argc, [rsp+8] is argv[0], and [rsp+16] is argv[1]."
    )

    all_derefs = [m for m in mov_operands if "[" in m[1]]
    assert len(all_derefs) >= 2, (
        "You need to dereference twice: once to get the argv[1] pointer from the stack,\n"
        "and once to read the value at that pointer!"
    )

    assert ['rax', '0x3c'] in mov_operands, (
        "You need to set rax to 60 (0x3c), the syscall number for exit!"
    )

    assert disas[-1].mnemonic == "syscall", (
        f"Your last instruction should be 'syscall', but you used '{disas[-1].mnemonic}'!"
    )

    return True

def check_runtime(filename):
    try:
        for _ in range(3):
            char = random.choice(string.ascii_letters + string.digits)
            expected = ord(char)

            print("")
            returncode = checker.dramatic_command(f"{filename} {char}")
            checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
            assert returncode == expected, (
                f"With argument '{char}', your program should exit with code {expected}, "
                f"but it exited with code {returncode}!"
            )
    finally:
        checker.dramatic_command("")
        print("")

    return True
