import __main__ as checker
import random
import string

give_flag = True
allow_asm = True
num_instructions = 5

check_disassembly_prologue = "Checking that your assembly compares the first byte of argv[1] against 'p'..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's run your program with different arguments to check the comparison!"
check_runtime_success = "Your program correctly compares the first character of argv[1] against 'p'! Nice work!"
check_runtime_failure = "Hmm, that's not right:\n"

def check_disassembly(disas):
	mov_operands = [d.op_str.split(", ") for d in disas if d.mnemonic == 'mov']

	has_argv1_deref = any(
		"[rsp + 0x10]" in src
		for _, src in mov_operands
	)
	assert has_argv1_deref, (
		"You need to load the argv[1] pointer from the stack using [rsp+16] (or [rsp+0x10])!\n"
		"Remember: [rsp] is argc, [rsp+8] is argv[0], and [rsp+16] is argv[1]."
	)

	has_cmp = any(d.mnemonic == 'cmp' for d in disas)
	assert has_cmp, (
		"You need to use the 'cmp' instruction to compare a byte against 'p' (0x70)!"
	)

	cmp_operands = [d.op_str for d in disas if d.mnemonic == 'cmp']
	has_byte_cmp = any("byte ptr" in op for op in cmp_operands)
	assert has_byte_cmp, (
		"You need to use BYTE PTR in your cmp instruction to compare a single byte!\n"
		"For example: cmp BYTE PTR [rax], 'p'"
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
		# Test with 'p' as first character: should exit 1 (match)
		print("")
		returncode = checker.dramatic_command(f"{filename} pwn")
		checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
		assert returncode == 1, (
			f"With argument 'pwn', the first character is 'p', "
			f"so your program should exit with 1, but it exited with {returncode}!"
		)

		# Test with non-'p' first characters: should exit 0 (no match)
		for arg in random.sample(["hello", "Xray", "abc", "zzz"], 2):
			print("")
			returncode = checker.dramatic_command(f"{filename} {arg}")
			checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
			assert returncode == 0, (
				f"With argument '{arg}', the first character is '{arg[0]}' (not 'p'), "
				f"so your program should exit with 0, but it exited with {returncode}!"
			)
	finally:
		checker.dramatic_command("")
		print("")

	return True
