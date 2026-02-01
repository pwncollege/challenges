import __main__ as checker
import subprocess
import time

give_flag = True
num_instructions = 8

FLAG_SIZE = 64

try:
	_flag = open("/flag").read().strip()
except FileNotFoundError:
	_flag = "pwn.college{test_placeholder_00000000000000}"

_flag_padded = (_flag + "\n").ljust(FLAG_SIZE, "\r")[:FLAG_SIZE]

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
		checker.print_prompt()
		checker.slow_print(f"{filename} <the flag>")

		result = subprocess.run(
			[filename, _flag_padded],
			capture_output=True,
			timeout=5
		)

		time.sleep(0.1)
		actual = result.stdout
		assert _flag.encode() in actual, (
			f"Your program should write the flag to stdout, but it wrote {actual!r}!"
		)

		if result.returncode < 0:
			assert False, f"Your program was killed by signal {-result.returncode}! Make sure to cleanly exit."
		checker.dramatic_command("echo $?", actual_command=f"echo {result.returncode}")
		assert result.returncode == 42, (
			f"Your program should exit with code 42, but it exited with {result.returncode}!"
		)
	except subprocess.TimeoutExpired:
		assert False, "Your program took too long to run! Make sure it exits."
	finally:
		checker.dramatic_command("")
		print("")

	return True
