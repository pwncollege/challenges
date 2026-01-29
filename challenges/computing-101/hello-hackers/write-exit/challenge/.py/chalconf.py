addr_chain = [ 1337000 ]
secret_checks = [ 'stdout' ]
secret_value = 0x48
exit_code = 42
secret_value_desc = "the letter H"
num_instructions = 8
must_set_regs = [ "rax", "rdi", "rsi", "rdx" ]
clean_exit = True
skip_deref_checks = True
success_message = """
YES! You wrote an 'H' and cleanly exited! Great job!
""".strip()
final_reg_vals = {
	"rax": (60, "syscall number of exit"),
	"rdi": (42, "the exit code we want"),
}
