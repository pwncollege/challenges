import random

addr_chain = [ random.randrange(0x1337000, 0x1338000), random.randrange(0x123400, 0x123500) ]
secret_addr_reg = 'rax'
must_set_regs = [ "rax", "rdi" ]
final_reg_vals = { "rax": 60 }
num_instructions = 4
