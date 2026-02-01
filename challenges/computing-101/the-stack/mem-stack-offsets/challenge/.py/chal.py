import __main__ as checker
import random

give_flag = True
num_instructions = 3

secret_value = random.randint(15, 255)
assembly_prefix = f"mov qword ptr [rsp+128], {secret_value}\n"

check_disassembly_prologue = "Checking that your assembly reads the secret value from the stack at offset 128 from rsp..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = f"Let's run your program and check that it exits with our secret value ({secret_value}) stored at [rsp+0x80]!"
check_runtime_success = "Neat! Your program correctly exits with the secret value! Great job!"
check_runtime_failure = "Hmm, that's not right:\n"

def check_disassembly(disas):
    mov_operands = [d.op_str.split(", ") for d in disas if d.mnemonic == 'mov']

    has_rsp_offset_deref = any(
        "[rsp + 0x80]" in src
        for _, src in mov_operands
    )
    assert has_rsp_offset_deref, (
        "You need to dereference rsp with an offset of 128 bytes (using [rsp+128] or [rsp+0x80])\n"
        "to read the secret value stored there!\n"
        "Remember: rsp points to the stack, and the secret value is 128 bytes into it."
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
        print("")
        returncode = checker.dramatic_command(filename)
        checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
        assert returncode == secret_value, (
            f"Your program exited with code {returncode}, but the secret value at [rsp+0x80] is {secret_value}!"
        )
    finally:
        checker.dramatic_command("")
        print("")

    return True
