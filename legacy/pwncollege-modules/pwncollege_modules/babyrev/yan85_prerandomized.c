#define SPEC_REG_A {{ challenge._shift_by("register_order", "a") }}
#define SPEC_REG_B {{ challenge._shift_by("register_order", "b") }}
#define SPEC_REG_C {{ challenge._shift_by("register_order", "c") }}
#define SPEC_REG_D {{ challenge._shift_by("register_order", "d") }}
#define SPEC_REG_S {{ challenge._shift_by("register_order", "s") }}
#define SPEC_REG_I {{ challenge._shift_by("register_order", "i") }}
#define SPEC_REG_F {{ challenge._shift_by("register_order", "f") }}

#define INST_IMM {{ challenge._shift_by("operation_order", "imm") }}
#define INST_STK {{ challenge._shift_by("operation_order", "stk") }}
#define INST_ADD {{ challenge._shift_by("operation_order", "add") }}
#define INST_STM {{ challenge._shift_by("operation_order", "stm") }}
#define INST_LDM {{ challenge._shift_by("operation_order", "ldm") }}
#define INST_JMP {{ challenge._shift_by("operation_order", "jmp") }}
#define INST_CMP {{ challenge._shift_by("operation_order", "cmp") }}
#define INST_SYS {{ challenge._shift_by("operation_order", "sys") }}

#define SYS_OPEN        {{ challenge._shift_by("syscall_order", "open") }}
#define SYS_READ_MEMORY {{ challenge._shift_by("syscall_order", "read_memory") }}
#define SYS_READ_CODE   {{ challenge._shift_by("syscall_order", "read_code") }}
#define SYS_WRITE       {{ challenge._shift_by("syscall_order", "write") }}
#define SYS_SLEEP       {{ challenge._shift_by("syscall_order", "sleep") }}
#define SYS_EXIT        {{ challenge._shift_by("syscall_order", "exit") }}

#define FLAG_L {{ challenge._shift_by("flag_order", "l") }}
#define FLAG_G {{ challenge._shift_by("flag_order", "g") }}
#define FLAG_E {{ challenge._shift_by("flag_order", "e") }}
#define FLAG_N {{ challenge._shift_by("flag_order", "n") }}
#define FLAG_Z {{ challenge._shift_by("flag_order", "z") }}

#define INST_TYPE {{ challenge.inst_definition}}
