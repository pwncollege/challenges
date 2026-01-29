import random

addr_chain = [ random.randrange(0x1337000, 0x1338000) ]
must_set_regs = [ "rax", "rdi" ]
final_reg_vals = { "rax": 60 }
secret_addr_reg = 'rax'
