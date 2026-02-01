import __main__ as checker
import tempfile
import time
import os

give_flag = False
num_instructions = 8

FLAG_SIZE = 64

try:
	_flag = open("/flag").read().strip()
except FileNotFoundError:
	_flag = "pwn.college{test_placeholder_00000000000000}"

_flag_padded = (_flag + "\n").ljust(FLAG_SIZE, "\r")[:FLAG_SIZE]
_flag_masked = "pwn.college{" + "*" * (len(_flag) - len("pwn.college{}")) + "}"

# Write padded flag to a temp file so the shell can pass it as argv[1]
_flag_arg_file = tempfile.mktemp(prefix='check_flag_')
with open(_flag_arg_file, 'wb') as f:
	f.write(_flag_padded.encode())

check_disassembly_prologue = "Checking that your assembly writes the first argument to stdout and exits..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's run your program with the flag as its first argument!"
check_runtime_success = "YES! You wrote the flag to stdout and cleanly exited! Great job!"
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

	assert ['rdx', '0x40'] in mov_operands, (
		"You need to set rdx to 64 (0x40), the number of bytes to write!"
	)

	assert ['rax', '0x3c'] in mov_operands, (
		"You need to set rax to 60 (0x3c), the syscall number for exit!"
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
			f"{filename} {_flag_masked}",
			actual_command=f"bash -c 'exec {filename} \"$(cat {_flag_arg_file})\" 2> >(tee /tmp/stderr 2>&1) > >(tee /tmp/stdout)'"
		)
		time.sleep(0.1)

		actual = open("/tmp/stdout", "rb").read()
		assert _flag.encode() in actual, (
			f"Your program should write the flag to stdout!"
		)

		checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
		assert returncode == 42, (
			f"Your program should exit with code 42, but it exited with {returncode}!"
		)
	finally:
		try:
			os.unlink(_flag_arg_file)
		except OSError:
			pass
		checker.dramatic_command("")
		print("")

	return True
