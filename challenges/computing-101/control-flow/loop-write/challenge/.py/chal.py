import __main__ as checker
import random
import shlex
import string

give_flag = True
allow_asm = True

check_disassembly_prologue = "Checking that your assembly contains a loop over argv[1]..."
check_disassembly_success = "Your assembly looks like it has a real loop!"
check_disassembly_failure = "There's an issue with your assembly:\n"

check_runtime_prologue = "Let's run your program with different arguments to check the length calculation!"
check_runtime_success = "Your program correctly computes the length of argv[1]!"
check_runtime_failure = "Hmm, that's not right:\n"


def _jump_target(insn):
	try:
		return int(insn.op_str, 0)
	except ValueError:
		return None


def _checks_zero(insn):
	operands = [operand.strip() for operand in insn.op_str.split(",")]
	if insn.mnemonic == "cmp":
		return any(operand in ("0", "0x0") for operand in operands)
	if insn.mnemonic == "test" and len(operands) == 2:
		return operands[0] == operands[1]
	return False


def check_disassembly(disas):
	mnemonics = [d.mnemonic for d in disas]
	mov_operands = checker.mov_operands(disas)

	has_argv1_deref = any("[rsp + 0x10]" in src for _, src in mov_operands)
	assert has_argv1_deref, (
		"You need to load the argv[1] pointer from the stack using [rsp+16] (or [rsp+0x10])!\n"
		"Remember: [rsp] is argc, [rsp+8] is argv[0], and [rsp+16] is argv[1]."
	)

	has_zero_check = any(_checks_zero(insn) for insn in disas)
	assert has_zero_check, (
		"Your loop needs to check for the null terminator at the end of argv[1].\n"
		"Compare the current byte against 0, or `test` it against itself, to decide when the loop is finished."
	)

	backward_jumps = [
		insn for insn in disas
		if insn.mnemonic.startswith("j") and _jump_target(insn) is not None and _jump_target(insn) < insn.address
	]
	assert backward_jumps, (
		"A loop repeats by jumping backward to earlier code.\n"
		"Use a label at the top of your loop and jump back to it after processing a byte."
	)

	has_progress = any(mnemonic in ("inc", "add", "lea") for mnemonic in mnemonics)
	assert has_progress, (
		"Your loop needs to make progress before it jumps back.\n"
		"Advance through the string and update the length as you go."
	)

	assert ["rax", "0x3c"] in mov_operands, (
		"You need to set rax to 60 (0x3c), the syscall number for exit!"
	)
	assert "syscall" in mnemonics, "Your program needs a syscall instruction to exit."

	return True


def check_runtime(filename):
	cases = ["", "p", "pwn", "loops", "pwn123", "two words", "symbols!?"]
	characters = string.ascii_letters + string.digits + string.punctuation + " "
	for _ in range(3):
		length = random.randint(2, 12)
		cases.append("".join(random.choice(characters) for _ in range(length)))

	for arg in cases:
		print("")
		command = f"{filename} {shlex.quote(arg)}"
		returncode = checker.dramatic_command(command)
		checker.dramatic_command("echo $?", actual_command=f"echo {returncode}")
		expected = len(arg)
		assert returncode == expected, (
			f"With argv[1] set to {arg!r}, the string length is {expected}, "
			f"so your program should exit with {expected}, but it exited with {returncode}."
		)

	return True
