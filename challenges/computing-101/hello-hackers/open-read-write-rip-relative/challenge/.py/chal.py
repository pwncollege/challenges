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

def check_raw_binary(raw):
	assert b"/flag\x00" in raw, (
		"Store the filename directly after your code as a null-terminated string:\n"
		'    path:\n'
		'        .asciz "/flag"'
	)
	return True

def split_operands(insn):
	return [op.strip() for op in insn.op_str.split(", ", 1)]

def normalize_reg(reg):
	return checker.SUBREG_TO_64.get(reg, reg)

def instruction_sets_reg(insn, reg, value):
	if not insn.op_str:
		return False

	if insn.mnemonic == "mov":
		dst, src = split_operands(insn)
		return normalize_reg(dst) == reg and normalize_reg(src) == value

	if value == "0" and insn.mnemonic == "xor":
		dst, src = split_operands(insn)
		return normalize_reg(dst) == reg and normalize_reg(src) == reg

	return False

def instruction_writes_reg(insn, reg):
	if insn.mnemonic not in {"lea", "mov", "xor"} or not insn.op_str:
		return False
	return normalize_reg(split_operands(insn)[0]) == reg

def rax_value_before(disas, idx):
	for insn in reversed(disas[:idx]):
		if instruction_sets_reg(insn, "rax", "0"):
			return "0"
		if insn.mnemonic == "mov" and insn.op_str:
			dst, src = split_operands(insn)
			if normalize_reg(dst) == "rax":
				return normalize_reg(src)
	return None

def assert_write_count_from_read(disas):
	syscalls = [i for i, insn in enumerate(disas) if insn.mnemonic == "syscall"]
	read_i = next((i for i in syscalls if rax_value_before(disas, i) == "0"), None)
	write_i = next((i for i in syscalls if rax_value_before(disas, i) == "1"), None)
	assert read_i is not None, "You need to invoke the read syscall (set rax to 0)!"
	assert write_i is not None, "You need to invoke the write syscall (set rax to 1)!"
	assert read_i < write_i, "You need to read the data before you write it back out!"

	rdx_writes_after_read = [
		insn
		for insn in disas[read_i + 1:write_i]
		if instruction_writes_reg(insn, "rdx")
	]
	assert rdx_writes_after_read and instruction_sets_reg(rdx_writes_after_read[-1], "rdx", "rax"), (
		"write's length (rdx) must come from read's return value (rax).\n"
		"read returns how many bytes it actually read, so after your read syscall do\n"
		"`mov rdx, rax` --- write exactly that many bytes --- rather than hardcoding a length."
	)

def check_disassembly(disas):
	mov_operands = checker.mov_operands(disas)
	syscall_indices = [i for i, insn in enumerate(disas) if insn.mnemonic == "syscall"]

	byte_stores = [dst for dst, _ in mov_operands if "byte ptr [rsp" in dst]
	assert not byte_stores, (
		"This level should not build the filename byte by byte on the stack.\n"
		"Store it with `.asciz` and load its address with `lea rdi, [rip + path]`."
	)

	assert syscall_indices, "You need to invoke the open syscall!"
	first_syscall = syscall_indices[0]

	rdi_writes = [
		(i, insn)
		for i, insn in enumerate(disas[:first_syscall])
		if instruction_writes_reg(insn, "rdi")
	]
	assert rdi_writes, (
		"Before open, load the filename address into rdi with `lea rdi, [rip + path]`!"
	)
	_, last_rdi_write = rdi_writes[-1]
	assert last_rdi_write.mnemonic == "lea" and split_operands(last_rdi_write)[1].startswith("[rip + "), (
		"Before open, the last value you put in rdi should come from a RIP-relative `lea`,\n"
		"such as `lea rdi, [rip + path]`."
	)

	assert ['rax', '2'] in mov_operands, (
		"You need to set rax to 2, the syscall number for open!"
	)

	assert any(instruction_sets_reg(insn, "rax", "0") for insn in disas), (
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
	assert_write_count_from_read(disas)

	exit_syscall = syscall_indices[-1]
	rax_writes_before_exit = [
		insn
		for insn in disas[:exit_syscall]
		if instruction_writes_reg(insn, "rax")
	]
	assert rax_writes_before_exit and split_operands(rax_writes_before_exit[-1])[1] == "0x3c", (
		"Before your final syscall, your last assignment to rax should be 60 (0x3c) for exit,\n"
		"but you're overwriting it afterwards!"
	)

	rdi_writes_before_exit = [
		insn
		for insn in disas[:exit_syscall]
		if instruction_writes_reg(insn, "rdi")
	]
	assert rdi_writes_before_exit and split_operands(rdi_writes_before_exit[-1])[1] == "0x2a", (
		"Before your final syscall, your last assignment to rdi should be 42 (0x2a) for the exit code!"
	)

	return True

def check_runtime(filename):
	# The program opens and reads the real /flag, so run it as root --- the privilege a
	# real flag-reading program holds for that protected (0400, root-owned) file. We
	# never relax the flag's permissions or rewrite it.
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
