import __main__ as checker
import os
import time

give_flag = False
num_instructions = 17

FLAG_SIZE = 64

check_disassembly_prologue = "Checking the assembly code..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's run your program and see if it can read the flag!"
check_runtime_success = "Your program opened, read, and wrote the flag!"
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

	assert ['rax', '2'] in mov_operands, (
		"You need to set rax to 2, the syscall number for open!"
	)

	assert ['rax', '0'] in mov_operands, (
		"You need to set rax to 0, the syscall number for read!"
	)

	assert ['rax', '1'] in mov_operands, (
		"You need to set rax to 1, the syscall number for write!"
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
		print("")

		# pad /flag to exactly FLAG_SIZE bytes so the student's program reads clean data
		os.seteuid(0)
		with open("/flag", "r") as f:
			flag_content = f.read().strip()
		padded = (flag_content + "\n"+"\r"*100)[:FLAG_SIZE]
		with open("/flag", "w") as f:
			f.write(padded)
		os.chmod("/flag", 0o644)
		os.seteuid(65534)

		returncode = checker.dramatic_command(f"{filename} /flag")

		checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
		assert returncode == 42, (
			f"Your program should exit with code 42, but it exited with {returncode}!"
		)
	finally:
		os.seteuid(0)
		os.chmod("/flag", 0o600)
		os.seteuid(65534)
		checker.dramatic_command("")
		print("")

	return True
