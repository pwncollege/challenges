import random

addr_chain = [ 567800, random.randrange(0x1337000, 0x1338000) ]
num_instructions = 4
must_set_regs = [ "rax", "rdi" ]
final_reg_vals = { "rax": 60 }
