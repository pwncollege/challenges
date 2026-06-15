import __main__ as checker
import tempfile
import time
import os

# Run the learner's own complete program as-is (executable mode --- no builder rebuild).
executable = True
give_flag = False

try:
	_flag = open("/flag").read().strip()
except FileNotFoundError:
	_flag = "pwn.college{test_placeholder_00000000000000}"

# Unlike the `read` level, we do NOT pad the input. The flag arrives at its real length,
# so a single hardcoded count would over- or under-shoot; the learner must write back
# exactly the number of bytes read() returned.
_flag_bytes = (_flag + "\n").encode()
_flag_masked = "pwn.college{" + "*" * (len(_flag) - len("pwn.college{}")) + "}"

_flag_stdin_file = tempfile.mktemp(prefix='check_flag_')
with open(_flag_stdin_file, 'wb') as f:
	f.write(_flag_bytes)

check_disassembly_prologue = "Checking the assembly code..."
check_disassembly_success = "Your assembly looks correct!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's pipe the flag in and check that you echo back exactly what you read!"
check_runtime_success = "YES! You wrote back exactly the bytes you read! Great job!"
check_runtime_failure = "Hmm, that's not right:\n"

def check_disassembly(disas):
	mov_operands = checker.mov_operands(disas)

	has_rsp_src = any(src == "rsp" for _, src in mov_operands)
	assert has_rsp_src, (
		"You need to use rsp as your memory address for read/write!\n"
		"Use 'mov rsi, rsp' to point rsi at the stack."
	)

	# The whole point of this level: write's length must be read's return value.
	checker.assert_write_count_from_read(disas)

	assert ['rdi', '0x2a'] in mov_operands, (
		"You need to set rdi to 42 (0x2a), the exit code!"
	)

	# Find the exit syscall by scanning, not by assuming it is the final instruction.
	syscall_indices = [i for i, insn in enumerate(disas) if insn.mnemonic == "syscall"]
	assert syscall_indices, "You need to invoke the exit syscall!"
	rax_before_exit = [m for m in checker.mov_operands(disas[:syscall_indices[-1]]) if m[0] == 'rax']
	assert rax_before_exit and rax_before_exit[-1] == ['rax', '0x3c'], (
		"Your last assignment to rax before the exit syscall should be 60 (0x3c),\n"
		"but you're overwriting it afterwards!"
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

		# The read->write pattern is enforced statically in check_disassembly; here we just
		# let the learner watch their own program echo the flag back out.
		actual_bytes = open("/tmp/stdout", "rb").read()
		assert _flag.encode() in actual_bytes, (
			"Your program should read the flag from stdin and write it back to stdout."
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
