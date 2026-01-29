import __main__ as checker

#pylint:disable=global-statement

allow_asm = False
num_instructions = 3
give_flag = True
returncode = None

check_runtime_prologue = """
\033[92mLet's check what your exit code is! It should be 42 to succeed!

Go go go!
\033[0m
""".strip()

check_runtime_success = """
\033[92m
Neat! Your program exited with the correct error code! But what
if it hadn't? Next, we'll learn about some simple debugging.
For now, take this with you:

\033[0m
""".strip()

check_runtime_failure = """
\033[0;31m
Your program exited with the wrong error code. Please make sure
to set 'rdi' to 42 (you exited with '{returncode}')!\033[0m
""".strip()

def check_disassembly(disas):
	assert disas[0].mnemonic == "mov" and disas[1].mnemonic == "mov", (
		"Your first two instructions must be 'mov' instructions: one to\n"
		"move a value into rdi, and one to move a value into rax.\n"
	)

	opnds1 = disas[0].op_str.split(", ")
	opnds2 = disas[1].op_str.split(", ")
	regs, _ = zip(opnds1, opnds2)
	assert set(regs) == { 'rax', 'rdi' }, (
		"You must set both the rax register and the rdi register!"
	)

	assert ( ['rax','0x3c'] in [ opnds1, opnds2 ] ), (
		"You must properly set the 'exit' system call number (60 in rax)!"
	)

	operation = disas[2].mnemonic
	assert operation == "syscall", (
		"Your last instruction should be the 'syscall' instruction to invoke\n"
		f"the exit system call, but you used the '{operation}' instruction!"
	)

	return True

def check_runtime(filename):
	global returncode
	returncode = checker.dramatic_command(filename)
	checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
	checker.dramatic_command("")
	assert returncode == 42
