import socket
import time
import sys
import os

import __main__ as checker

allow_asm = True
num_instructions = 2
give_flag = True

def check_disassembly(disas):
	operation = disas[0].mnemonic
	assert operation == "mov", (
		"Your first instruction's operation must be 'mov', "
		f"but yours was {operation}."
	)

	opnd1, opnd2 = disas[0].op_str.split(", ")
	assert opnd1 == "rax", (
		"You must move your system call index to the 'rax' register, "
		f"but you are moving to {opnd1}."
	)

	try:
		assert int(opnd2, 0) == 60, (
			"You must move the syscall index of exit (60) into rax, "
			f"whereas you moved {int(opnd2, 0)}."
		)
	except ValueError as e:
		if opnd2.startswith("r"):
			raise AssertionError(
				"It looks like you are trying to move values from one register\n"
				"to another, rather than specifying a number to move to rax.\n"
				"Try moving 60 to rax!"
			) from e
		raise AssertionError(
			"You must move the syscall index of exit (60) into rax, whereas\n"
			f"you instead specified {opnd2}."
		) from e

	operation = disas[1].mnemonic
	assert operation == "syscall", (
		"Your second instruction should be the 'syscall' instruction to invoke\n"
		f"the exit system call, but you used the '{operation}' instruction!"
	)

	return True

def check_runtime(filename):
	checker.dramatic_command(filename)
	checker.dramatic_command("")

check_runtime_prologue = """
\033[92mOkay, now you have written your first COMPLETE program!
All it'll do is exit, but it'll do so cleanly, and we can
build from there!

Let's see what happens when you run it:
\033[0m
""".strip()

check_runtime_success = """
\033[92m
Neat! Your program exited cleanly! Let's push on to make things
more interesting! Take this with you:
\033[0m
""".strip()
