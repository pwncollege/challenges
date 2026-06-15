import __main__ as checker
import os

# Run the learner's own complete program as-is (executable mode --- no builder rebuild),
# so it executes with exactly the privileges we give it rather than the builder's SUID
# wrapper. These levels need the program to read the real /flag, so we run it as root.
executable = True
give_flag = False

check_disassembly_prologue = "Checking the assembly code..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's run your program and see if it can read the flag!"
check_runtime_success = "Your program opened, read, and wrote the flag!"
check_runtime_failure = "Hmm, that's not right:\n"

def check_disassembly(disas):
	mov_operands = checker.mov_operands(disas)

	byte_stores = [dst for dst, _ in mov_operands if "byte ptr [rsp" in dst]
	assert len(byte_stores) >= 6, (
		"You need to write the filename '/flag\\0' byte by byte onto the stack!\n"
		'Use instructions such as "mov BYTE PTR [rsp], \'/\'", one byte per character, plus the null terminator.'
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

	# Write back exactly what you read: write's length (rdx) must come from read's
	# return value (rax), the idiom you learned in read-exact --- not a hardcoded count.
	checker.assert_write_count_from_read(disas)

	# Find the exit syscall (the last syscall) by scanning, not by assuming it is the
	# final instruction --- a program may legitimately store data after its code. The
	# last rax written before that syscall must be 60 (0x3c) for exit.
	syscall_indices = [i for i, insn in enumerate(disas) if insn.mnemonic == "syscall"]
	assert syscall_indices, "You need to invoke the exit syscall!"
	rax_before_exit = [m for m in checker.mov_operands(disas[:syscall_indices[-1]]) if m[0] == 'rax']
	assert rax_before_exit and rax_before_exit[-1] == ['rax', '0x3c'], (
		"Your last assignment to rax before the exit syscall should be 60 (0x3c),\n"
		"but you're overwriting it afterwards!"
	)

	return True

def check_runtime(filename):
	# The program opens and reads the real /flag, so run it as root --- the privilege a
	# real flag-reading program holds for that protected (0400, root-owned) file. We
	# never relax the flag's permissions.
	saved_ids = os.getresuid()
	try:
		print("")

		os.setresuid(0, 0, 0)
		returncode = checker.dramatic_command(filename)

		checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
		assert returncode == 42, (
			f"Your program should exit with code 42, but it exited with {returncode}!"
		)
	finally:
		os.setresuid(*saved_ids)
		checker.dramatic_command("")
		print("")

	return True
