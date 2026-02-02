import subprocess
import __main__ as checker

allow_asm = False
give_flag = True

check_disassembly_prologue = "Checking that your program uses int3 for cooperative debugging..."
check_disassembly_success = "... found int3! Your program is ready to cooperate with the debugger."
check_disassembly_failure = "... your program needs to use the int3 instruction!\n"

def check_disassembly(disas):
	mnemonics = [i.mnemonic for i in disas]
	assert "int3" in mnemonics, (
		"Your program must include the 'int3' instruction to cooperatively "
		"signal the debugger. This is the x86 software breakpoint instruction."
	)
	return True

check_runtime_prologue = "Running your program under gdb to test cooperative debugging..."
check_runtime_success = "... $rdi is 1337 at the int3 trap! Cooperative debugging works!"
check_runtime_failure = "... something went wrong during cooperative debugging.\n"

def check_runtime(filename):
	result = subprocess.run(
		["/usr/bin/gdb", "-batch",
		 "-ex", "set disable-randomization off",
		 "-ex", "run",
		 "-ex", "print/d $rdi",
		 filename],
		capture_output=True, text=True, timeout=10
	)
	output = result.stdout + result.stderr

	assert "SIGTRAP" in output, (
		"Your program did not trigger a SIGTRAP. The int3 instruction should "
		"cause a SIGTRAP signal that the debugger catches. Make sure your "
		"program actually executes int3!"
	)

	for line in result.stdout.split('\n'):
		if line.strip().startswith('$') and '=' in line:
			val_str = line.split('=')[1].strip()
			val = int(val_str)
			assert val == 1337, (
				f"Expected $rdi to be 1337, but it was {val}. "
				"Make sure you set rdi to 1337 before executing int3."
			)
			return True

	assert False, "Could not read the $rdi register value from GDB output."
