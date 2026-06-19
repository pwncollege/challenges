import __main__ as checker
import random

give_flag = True
allow_asm = True

check_disassembly_prologue = "Checking that your assembly uses conditional jumps..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's run your program with different arguments to check the conditional jump!"
check_runtime_success = "Your program correctly uses jne to branch on the comparison! Nice work!"
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

	# Must have a cmp instruction
	has_cmp = 'cmp' in mnemonics
	assert has_cmp, (
		"You need to use the 'cmp' instruction to compare a byte against 'p' (0x70)!"
	)

	# The cmp must use BYTE PTR (single-byte comparison)
	cmp_operands = [d.op_str for d in disas if d.mnemonic == 'cmp']
	has_byte_cmp = any("byte ptr" in op for op in cmp_operands)
	assert has_byte_cmp, (
		"You need to use BYTE PTR in your cmp instruction to compare a single byte!\n"
		"For example: cmp BYTE PTR [rax], 'p'"
	)

	# Must use jne/jnz (not setz/setnz)
	has_jne = any(m in ('jne', 'jnz') for m in mnemonics)
	assert has_jne, (
		"You need to use 'jne' to jump to the failure case!\n"
		"This is a conditional jump that jumps when the compared values are NOT equal."
	)

	has_setcc = any(m in ('setne', 'sete', 'setnz', 'setz') for m in mnemonics)
	assert not has_setcc, (
		"You're using setz/setnz, but this challenge wants you to use 'jne' instead!\n"
		"Instead of capturing the flag into a register, jump to a different code path."
	)

	# The jne must come after the cmp (compare then branch)
	cmp_idx = mnemonics.index('cmp')
	jne_idx = next(i for i, m in enumerate(mnemonics) if m in ('jne', 'jnz'))
	assert jne_idx > cmp_idx, (
		"Your 'jne' should come after the 'cmp'!\n"
		"First compare, then branch based on the result."
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

	# Should set rdi to 0 (success) on one path and 1 (failure) on the other.
	# Accept mov rdi, 0 / mov edi, 0 / xor rdi, rdi / xor edi, edi for zero.
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

	# The jne target should jump forward past the success path to the failure path.
	jne_insn = next(d for d in disas if d.mnemonic in ('jne', 'jnz'))
	jne_target = int(jne_insn.op_str, 0)
	assert jne_target > jne_insn.address, (
		"Your 'jne' should jump forward to the failure label, not backward!\n"
		"The structure should be: compare, jne fail, [success path], fail: [failure path]."
	)

	return True

def check_runtime(filename):
	# Test with 'p' as first character: should exit 0 (success/match)
	print("")
	returncode = checker.dramatic_command(f"{filename} pwn")
	checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
	assert returncode == 0, (
		f"With argument 'pwn', the first character is 'p' (equal!), "
		f"so your program should exit with 0, but it exited with {returncode}!\n"
		"Remember: the success path (equal) should exit(0), and jne should jump to the failure path."
	)

	# Test with non-'p' first characters: should exit 1 (failure/no match)
	for arg in random.sample(["hello", "hackers", "abc", "college"], 2):
		returncode = checker.dramatic_command(f"{filename} {arg}")
		checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
		assert returncode == 1, (
			f"With argument '{arg}', the first character is '{arg[0]}' (not equal to 'p'), "
			f"so your program should exit with 1, but it exited with {returncode}!\n"
			"Remember: jne should jump to the 'fail' label which exits with 1."
		)

	return True
