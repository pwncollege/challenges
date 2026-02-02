import __main__ as checker
import random

give_flag = True
allow_asm = True

check_disassembly_prologue = "Checking that your assembly compares multiple characters of argv[1]..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's run your program with different arguments to check the string comparison!"
check_runtime_success = "Your program correctly checks for the string \"pwn\"! Nice work!"
check_runtime_failure = "Hmm, that's not right:\n"

def check_disassembly(disas):
	mnemonics = [d.mnemonic for d in disas]
	mov_operands = [d.op_str.split(", ") for d in disas if d.mnemonic == 'mov']

	# Must load argv[1] pointer from stack
	has_argv1_deref = any(
		"[rsp + 0x10]" in src
		for _, src in mov_operands
	)
	assert has_argv1_deref, (
		"You need to load the argv[1] pointer from the stack using [rsp+16] (or [rsp+0x10])!\n"
		"Remember: [rsp] is argc, [rsp+8] is argv[0], and [rsp+16] is argv[1]."
	)

	# Must have multiple cmp instructions (one per character: 'p', 'w', 'n')
	cmp_instructions = [d for d in disas if d.mnemonic == 'cmp']
	assert len(cmp_instructions) >= 3, (
		f"You need at least 3 'cmp' instructions (one for each character of \"pwn\"), "
		f"but you only have {len(cmp_instructions)}!"
	)

	# Each cmp must use BYTE PTR (single-byte comparison)
	for cmp_insn in cmp_instructions:
		assert "byte ptr" in cmp_insn.op_str, (
			f"Each character comparison must use BYTE PTR!\n"
			f"Found: cmp {cmp_insn.op_str}\n"
			f"Expected something like: cmp BYTE PTR [rax], 'p'"
		)

	# Must use jne/jnz (not setz/setnz)
	jne_instructions = [d for d in disas if d.mnemonic in ('jne', 'jnz')]
	assert len(jne_instructions) >= 3, (
		f"You need at least 3 'jne' instructions (one after each 'cmp'), "
		f"but you only have {len(jne_instructions)}!\n"
		"Each character comparison should be followed by a 'jne fail' to jump on mismatch."
	)

	has_setcc = any(m in ('setne', 'sete', 'setnz', 'setz') for m in mnemonics)
	assert not has_setcc, (
		"You're using setz/setnz, but this challenge wants you to use 'jne' instead!\n"
		"Use multiple cmp/jne pairs to check each character."
	)

	# All jne instructions should jump to the same target (the fail label)
	jne_targets = set(int(d.op_str, 0) for d in jne_instructions)
	assert len(jne_targets) == 1, (
		"All your 'jne' instructions should jump to the same failure label!\n"
		f"But your jne instructions jump to {len(jne_targets)} different targets.\n"
		"Use a single 'fail:' label and have every jne point to it."
	)

	# Each jne must come after a cmp
	for jne_insn in jne_instructions:
		jne_idx = list(disas).index(jne_insn)
		assert jne_idx > 0 and disas[jne_idx - 1].mnemonic == 'cmp', (
			"Each 'jne' should immediately follow a 'cmp' instruction!\n"
			"Pattern: cmp BYTE PTR [rax+N], 'char' followed by jne fail."
		)

	# Must have two exit paths, each ending with syscall
	syscall_count = mnemonics.count('syscall')
	assert syscall_count >= 2, (
		f"Your program should have two exit paths (success and failure), each ending with 'syscall'.\n"
		f"You have {syscall_count} syscall instruction(s), but need at least 2."
	)

	# Must set up the exit syscall number
	assert ['rax', '0x3c'] in mov_operands, (
		"You need to set rax to 60 (0x3c), the syscall number for exit!"
	)

	# Should set rdi to 0 (success) and 1 (failure)
	sets_rdi_zero = (
		any(dst in ('rdi', 'edi') and src == '0' for dst, src in mov_operands) or
		any(d.mnemonic == 'xor' and d.op_str in ('rdi, rdi', 'edi, edi') for d in disas)
	)
	sets_rdi_one = any(
		dst in ('rdi', 'edi') and src == '1'
		for dst, src in mov_operands
	)
	assert sets_rdi_zero, (
		"Your success path should set rdi to 0 before calling exit.\n"
		"Use 'mov rdi, 0' (or 'xor rdi, rdi') for the success exit code."
	)
	assert sets_rdi_one, (
		"Your failure path should set rdi to 1 before calling exit.\n"
		"Use 'mov rdi, 1' for the failure exit code."
	)

	return True

def check_runtime(filename):
	# Test with "pwn" as argument: should exit 0 (all characters match)
	print("")
	returncode = checker.dramatic_command(f"{filename} pwn")
	checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
	assert returncode == 0, (
		f"With argument 'pwn', all three characters match ('p', 'w', 'n'), "
		f"so your program should exit with 0, but it exited with {returncode}!\n"
		"Remember: if all comparisons pass, execution falls through to exit(0)."
	)

	# Test with "pwnage": should also exit 0 (starts with "pwn")
	print("")
	returncode = checker.dramatic_command(f"{filename} pwnage")
	checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
	assert returncode == 0, (
		f"With argument 'pwnage', the first three characters are 'p', 'w', 'n' (all match!), "
		f"so your program should exit with 0, but it exited with {returncode}!"
	)

	# Test with strings that fail at different positions
	fail_cases = [
		("hello", "h", "the very first character"),
		("xwn", "x", "the first character"),
		("pan", "a", "the second character"),
		("pwd", "d", "the third character"),
	]
	for arg, bad_char, position in random.sample(fail_cases, 2):
		print("")
		returncode = checker.dramatic_command(f"{filename} {arg}")
		checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
		assert returncode == 1, (
			f"With argument '{arg}', {position} doesn't match, "
			f"so your program should exit with 1, but it exited with {returncode}!\n"
			"Remember: if any character doesn't match, jne should jump to 'fail' which exits with 1."
		)

	return True
