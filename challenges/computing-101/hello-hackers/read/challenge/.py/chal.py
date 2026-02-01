import __main__ as checker
import tempfile
import time
import os

give_flag = False
num_instructions = 13

FLAG_SIZE = 64

try:
	_flag = open("/flag").read().strip()
except FileNotFoundError:
	_flag = "pwn.college{test_placeholder_00000000000000}"

_flag_padded = (_flag + "\n").ljust(FLAG_SIZE, "\r")[:FLAG_SIZE]
_flag_masked = "pwn.college{" + "*" * (len(_flag) - len("pwn.college{}")) + "}"

# Write padded flag to a temp file so the shell can pipe it as stdin
_flag_stdin_file = tempfile.mktemp(prefix='check_flag_')
with open(_flag_stdin_file, 'wb') as f:
	f.write(_flag_padded.encode())

check_disassembly_prologue = "Checking the assembly code..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's pipe the flag into your program and check that it echoes it back!"
check_runtime_success = "YES! You read and wrote the flag! Great job!"
check_runtime_failure = "Hmm, that's not right:\n"

must_set_regs = [ "rax", "rdi", "rsi", "rdx" ]

def check_disassembly(disas):
	mov_operands = [d.op_str.split(", ") for d in disas if d.mnemonic == 'mov']

	set_regs = [dst for dst, _ in mov_operands]
	assert set(set_regs) >= set(must_set_regs), (
		"You must set each of the following registers (using the mov instruction):\n    "
		+ ", ".join(must_set_regs)
	)

	has_rsp_src = any(src == "rsp" for _, src in mov_operands)
	assert has_rsp_src, (
		"You need to use rsp as your memory address for read/write!\n"
		"Use 'mov rsi, rsp' to point rsi at the stack."
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
		returncode = checker.dramatic_command(
			f"echo {_flag_masked} | {filename}",
			actual_command=f"bash -c 'cat {_flag_stdin_file} | {filename} 2> >(tee /tmp/stderr 2>&1) > >(tee /tmp/stdout)'"
		)
		time.sleep(0.1)

		actual_bytes = open("/tmp/stdout", "rb").read()
		assert actual_bytes == _flag_padded.encode(), (
			f"Your program should echo the flag to stdout!"
		)

		checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
		assert returncode == 42, (
			f"Your program should exit with code 42, but it exited with {returncode}!"
		)
	finally:
		try:
			os.unlink(_flag_stdin_file)
		except OSError:
			pass
		checker.dramatic_command("")
		print("")

	return True
