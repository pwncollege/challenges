import __main__ as checker
import random

give_flag = True
num_instructions = 3

check_disassembly_prologue = "Checking that your assembly uses pop to read from the stack..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's run your program with different numbers of arguments to check that it correctly pops argc from the stack!"
check_runtime_success = "Neat! Your program correctly exits with the argument count every time! Great job!"
check_runtime_failure = "Hmm, that's not right:\n"

def check_disassembly(disas):
    mnemonics = [d.mnemonic for d in disas]
    operands = [d.op_str for d in disas]

    assert 'pop' in mnemonics, (
        "You need to use the 'pop' instruction to read from the stack!"
    )

    pop_idx = mnemonics.index('pop')
    assert operands[pop_idx] == 'rdi', (
        f"You should pop into rdi (the exit code register), but you popped into {operands[pop_idx]}."
    )

    mov_operands = [d.op_str.split(", ") for d in disas if d.mnemonic == 'mov']
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
