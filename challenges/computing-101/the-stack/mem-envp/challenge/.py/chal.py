import __main__ as checker
import random
import string

give_flag = True
num_instructions = 4

check_disassembly_prologue = "Checking that your assembly reads the envp[0] pointer from the stack..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's run your program with different first env vars to check that it reads the first byte of envp[0]!"
check_runtime_success = "Neat! Your program correctly exits with the first byte of envp[0] every time! Great job!"
check_runtime_failure = "Hmm, that's not right:\n"


def check_disassembly(disas):
    mov_operands = [d.op_str.split(", ") for d in disas if d.mnemonic == "mov"]

    has_envp_deref = any("[rsp + 0x18]" in src for _, src in mov_operands)
    assert has_envp_deref, (
        "You need to dereference rsp with an offset of 24 bytes (using [rsp+24] or [rsp+0x18])\n"
        "to read the envp[0] pointer stored on the stack!\n"
        "Remember: [rsp]=argc, [rsp+8]=argv[0], [rsp+16]=NULL (end of argv), [rsp+24]=envp[0]."
    )

    all_derefs = [d for d in disas if "[" in d.op_str]
    assert len(all_derefs) >= 2, (
        "You need to dereference twice: once to get the envp[0] pointer from the stack,\n"
        "and once to read the first byte of the env var string!"
    )

    assert ["rax", "0x3c"] in mov_operands, "You need to set rax to 60 (0x3c), the syscall number for exit!"

    assert (
        disas[-1].mnemonic == "syscall"
    ), f"Your last instruction should be 'syscall', but you used '{disas[-1].mnemonic}'!"

    return True


def check_runtime(filename):
    try:
        for _ in range(3):
            char = random.choice(string.ascii_uppercase)
            expected = ord(char)

            print("")
            cmd = f"env -i {char}=hello {filename}"
            returncode = checker.dramatic_command(cmd)
            checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
            assert returncode == expected, (
                f"With envp[0]='{char}=hello', your program should exit with code {expected} "
                f"(the byte for '{char}'), but it exited with code {returncode}!"
            )
    finally:
        checker.dramatic_command("")
        print("")

    return True
