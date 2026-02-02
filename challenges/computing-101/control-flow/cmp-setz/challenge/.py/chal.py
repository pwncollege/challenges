import __main__ as checker
import random

give_flag = True
num_instructions = 5

check_disassembly_prologue = "Checking that your assembly compares argc against 42..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's run your program with different numbers of arguments to check the comparison!"
check_runtime_success = "Your program correctly uses cmp and setz to compare argc against 42! Nice work!"
check_runtime_failure = "Hmm, that's not right:\n"

def check_disassembly(disas):
	mov_operands = [d.op_str.split(", ") for d in disas if d.mnemonic == 'mov']
	cmp_operands = [d.op_str for d in disas if d.mnemonic == 'cmp']

	has_rsp_in_mov = any("[rsp]" in src for _, src in mov_operands)
	has_rsp_in_cmp = any("[rsp]" in op for op in cmp_operands)
	assert has_rsp_in_mov or has_rsp_in_cmp, (
		"You need to access the argument count from the top of the stack using [rsp]!\n"
		"Remember: [rsp] contains argc when your program starts.\n"
		"You can either load it into a register first (mov rdi, [rsp]) or compare directly (cmp QWORD PTR [rsp], 42)."
	)

	has_cmp = len(cmp_operands) > 0
	assert has_cmp, (
		"You need to use the 'cmp' instruction to compare a value with 42!"
	)

	has_setcc = any(
		d.mnemonic in ('setne', 'sete') and d.op_str == 'dil'
		for d in disas
	)
	assert has_setcc, (
		"You need to use 'setz dil' (or 'setnz dil') to store the comparison result\n"
		"into the lower byte of rdi! Remember: dil is the lower 8 bits of rdi."
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
		# Test with 42 args (argc = 42): should exit 1 (match)
		args = " ".join("a" for _ in range(41))
		print("")
		returncode = checker.dramatic_command(f"{filename} {args}")
		checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
		assert returncode == 1, (
			f"With 42 total arguments (program name + 41 args), argc is 42, "
			f"so your program should exit with 1, but it exited with {returncode}!"
		)

		# Test with non-42 arg counts: should exit 0 (no match)
		for num_extra in random.sample([0, 3, 15, 45], 2):
			argc = num_extra + 1
			args = " ".join("a" for _ in range(num_extra))
			cmd = f"{filename} {args}".strip()
			print("")
			returncode = checker.dramatic_command(cmd)
			checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
			assert returncode == 0, (
				f"With {argc} total argument(s) (argc = {argc}, not 42), "
				f"your program should exit with 0, but it exited with {returncode}!"
			)
	finally:
		checker.dramatic_command("")
		print("")

	return True
