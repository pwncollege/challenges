import __main__ as checker
import random
import string
import time

give_flag = True
num_instructions = 8

check_disassembly_prologue = "Checking that your assembly writes a byte from the first argument and exits..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's run your program with different arguments to check that it writes and exits!"
check_runtime_success = "YES! You wrote a character and cleanly exited! Great job!"
check_runtime_failure = "Hmm, that's not right:\n"

def check_disassembly(disas):
	mov_operands = [d.op_str.split(", ") for d in disas if d.mnemonic == 'mov']

	has_argv1_deref = any(
		"[rsp + 0x10]" in src
		for _, src in mov_operands
	)
	assert has_argv1_deref, (
		"You need to load the first argument's address from the stack using [rsp+16]\n"
		"(or [rsp+0x10])!"
	)

	assert ['rax', '0x3c'] in mov_operands, (
		"You need to set rax to 60 (0x3c), the syscall number for exit!"
	)
	assert ['rdi', '0x2a'] in mov_operands, (
		"You need to set rdi to 42 (0x2a), the exit code!"
	)

	last_rax = max(i for i, m in enumerate(mov_operands) if m[0] == 'rax')
	assert mov_operands[last_rax] == ['rax', '0x3c'], (
		"Your last assignment to rax should be 60 (0x3c) for the exit syscall,\n"
		"but you're overwriting it afterwards!"
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

			checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
			assert returncode == 42, (
				f"Your program should exit with code 42, but it exited with {returncode}!"
			)
	finally:
		checker.dramatic_command("")
		print("")

	return True
