import __main__ as checker
import os
import shlex

give_flag = False

check_disassembly_prologue = "Checking the assembly code..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's run your program and see if it can read the flag!"
check_runtime_success = "Your program opened, read, and wrote the flag!"
check_runtime_failure = "Hmm, that's not right:\n"

def check_disassembly(disas):
	mov_operands = checker.mov_operands(disas)

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
	stdout_path = "/tmp/open-read-write.stdout"
	try:
		print("")

		os.seteuid(0)
		try:
			os.unlink(stdout_path)
		except FileNotFoundError:
			pass
		os.chmod("/flag", 0o644)
		os.seteuid(65534)

		run_and_capture = f"exec {shlex.quote(filename)} /flag | tee {shlex.quote(stdout_path)}"
		returncode = checker.dramatic_command(
			f"{filename} /flag",
			actual_command=f"bash -o pipefail -c {shlex.quote(run_and_capture)}",
		)

		checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
		assert returncode == 42, (
			f"Your program should exit with code 42, but it exited with {returncode}!"
		)

		try:
			actual = open(stdout_path, "rb").read()
		except FileNotFoundError:
			actual = b""
		assert checker.read_flag() in actual, (
			"Your program exited correctly, but it did not write the flag to stdout!\n"
			"Make sure `write` uses the same buffer that `read` filled."
		)
	finally:
		os.seteuid(0)
		os.chmod("/flag", 0o600)
		try:
			os.unlink(stdout_path)
		except FileNotFoundError:
			pass
		os.seteuid(65534)
		checker.dramatic_command("")
		print("")

	return True
