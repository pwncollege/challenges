import __main__ as checker
import random
import string
import time

give_flag = True
num_instructions = 5

check_disassembly_prologue = "Checking that your assembly writes a byte from the first argument..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's run your program with different arguments to check that it writes a character!"
check_runtime_success = """
Wow, you wrote a character from the program's first argument to stdout!!!!!!! But why did your
program crash? Well, you didn't exit, and as before, the CPU kept executing and eventually crashed.
In the next level, we will learn how to chain two system calls together: write and exit!
""".strip()
check_runtime_failure = "Hmm, that's not right:\n"

def check_disassembly(disas):
	mov_operands = [d.op_str.split(", ") for d in disas if d.mnemonic == 'mov']

	has_argv1_deref = any(
		"[rsp + 0x10]" in src
		for _, src in mov_operands
	)
	assert has_argv1_deref, (
		"You need to load the first argument's address from the stack using [rsp+16]\n"
		"(or [rsp+0x10])! This is where the pointer to your program's first argument\n"
		"lives in memory."
	)

	assert ['rax', '1'] in mov_operands, (
		"You need to set rax to 1, the syscall number for write!"
	)
	assert ['rdi', '1'] in mov_operands, (
		"You need to set rdi to 1, the file descriptor for stdout!"
	)
	assert ['rdx', '1'] in mov_operands, (
		"You need to set rdx to 1, the number of bytes to write!"
	)

	assert disas[-1].mnemonic == "syscall", (
		f"Your last instruction should be 'syscall', but you used '{disas[-1].mnemonic}'!"
	)

	return True

def check_runtime(filename):
	try:
		for _ in range(3):
			char = random.choice(string.ascii_letters + string.digits)

			print("")
			returncode = checker.dramatic_command(
				f"{filename} {char}",
				actual_command=f"bash -c 'exec {filename} {char} 2> >(tee /tmp/stderr 2>&1) > >(tee /tmp/stdout)'"
			)
			time.sleep(0.1)
			actual = open("/tmp/stdout", "rb").read()
			assert actual == char.encode(), (
				f"With argument '{char}', your program should write '{char}' to stdout, "
				f"but it wrote {actual!r}!"
			)
	finally:
		checker.dramatic_command("")
		print("")

	return True
