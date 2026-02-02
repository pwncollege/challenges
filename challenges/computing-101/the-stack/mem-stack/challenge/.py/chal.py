import __main__ as checker
import random

give_flag = True
num_instructions = 3

check_disassembly_prologue = "Checking that your assembly reads the argument count from the top of the stack..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's run your program with different numbers of arguments to check that it correctly reads argc from [rsp]!"
check_runtime_success = "Neat! Your program correctly exits with the argument count every time! Great job!"
check_runtime_failure = "Hmm, that's not right:\n"

def check_disassembly(disas):
    mov_operands = [d.op_str.split(", ") for d in disas if d.mnemonic == 'mov']

    has_rsp_deref = any("[rsp]" in src for _, src in mov_operands)
    assert has_rsp_deref, (
        "You need to dereference rsp (using [rsp]) to read the value at the top of the stack!\n"
        "Remember: rsp contains the *address* of the data. [rsp] reads the data at that address."
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
            num_extra_args = random.randint(1, 10)
            args = " ".join(f"arg{i}" for i in range(num_extra_args))
            argc = num_extra_args + 1  # +1 for the program name

            print("")
            returncode = checker.dramatic_command(f"{filename} {args}")
            checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
            assert returncode == argc, (
                f"With {num_extra_args} extra argument(s) (plus the program name), argc should be {argc}, "
                f"but your program exited with code {returncode}!"
            )
    finally:
        checker.dramatic_command("")
        print("")

    return True
