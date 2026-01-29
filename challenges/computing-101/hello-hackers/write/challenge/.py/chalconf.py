addr_chain = [ 1337000 ]
secret_checks = [ 'stdout' ]
secret_value = 0x48
secret_value_desc = "the letter H"
num_instructions = 5
must_set_regs = [ "rax", "rdi", "rsi", "rdx" ]
final_reg_vals = {
	"rax": (1, "syscall number of write"),
	"rdi": (1, "fd of standard output"),
	"rsi": (addr_chain[0], "the address where the secret value is stored"),
	"rdx": (1, "just write a single byte")
}
clean_exit = False
skip_deref_checks = True
success_message = """
Wow, you wrote an "H"!!!!!!! But why did your program crash? Well, you didn't
exit, and as before, the CPU kept executing and eventually crashed. In the next
level, we will learn how to chain two system calls together: write and exit!
"""
