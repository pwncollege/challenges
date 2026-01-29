import __main__ as checker

allow_asm = True
num_instructions = 1
give_flag = True

def check_disassembly(disas):
	operation = disas[0].mnemonic
	assert operation == "mov", (
		f"Your instruction's operation must be 'mov', but yours was {operation}."
	)

	opnd1, opnd2 = disas[0].op_str.split(", ")
	assert opnd1 == "rax", (
		"You must move your data to the 'rax' register, but you are moving "
		f"to {opnd1}."
	)

	try:
		assert int(opnd2, 0) == 60, (
			"You must move the value 60 into rax, whereas you moved "
			f"{int(opnd2, 0)}."
		)
	except ValueError as e:
		if opnd2.startswith("r"):
			raise AssertionError(
				"It looks like you are trying to move values from one register\n"
				"to another, rather than specifying a number to move to rax.\n"
				"Try moving 60 to rax!"
			) from e
		raise AssertionError(
			"You must move the value 60 into rax, whereas you instead specified "
			f"{opnd2}."
		) from e

	return True

def check_runtime(filename):
	checker.dramatic_command(filename)
	checker.dramatic_command("")

check_runtime_prologue = """
\033[92m
Congratulations, you have written your first program!
Now let's see what happens when you run it:
\033[0m
""".strip()

check_runtime_success = """
\033[92m
... uh oh. The program crashed! We'll go into more details about
what a Segmentation Fault is later, but in this case, the program
crashed because, after the CPU moved the value 60 into rax, it was
never instructed to stop execution. With no further instructions
to execute, and no directive to stop, it crashed.

In the next level, we'll learn about how to stop program execution.
For now, here is your flag for your first (crashing) program!
\033[0m
""".strip()
