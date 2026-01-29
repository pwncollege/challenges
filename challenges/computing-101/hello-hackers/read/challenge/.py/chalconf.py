import random
import string

addr_chain = [ 1337000 ]
secret_checks = [ 'cat' ]
stdin = "".join(random.sample(string.ascii_letters, 8)).encode()
num_instructions = 13
read_size = 8
exit_code = 42
secret_value_reg = None
must_set_regs = [ "rax", "rdi", "rsi", "rdx" ]
clean_exit = True
skip_deref_checks = True
success_message = """
YES! You wrote the data and cleanly exited! Great job!
""".strip()
final_reg_vals = {
	"rax": (60, "syscall number of exit"),
	"rdi": (42, "the exit code we want"),
}
