import random

addr_chain = [
	random.randrange(0x1337000, 0x1338000),
	random.randrange(0x123400, 0x123500),
	random.randrange(0x100000, 0x101000)
]
secret_addr_reg = 'rdi'
num_instructions = 5
must_set_regs = [ "rax", "rdi" ]
final_reg_vals = { "rax": 60 }
