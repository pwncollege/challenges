#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/proc_fs.h>
#include <linux/mm.h>
#include <linux/cred.h>
#include <linux/vmalloc.h>
#include <linux/frame.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("pwn.college");
MODULE_DESCRIPTION("pwn.college challenge");
MODULE_VERSION("1.0");

#define MAX_FDS 8
#define SECCOMP_VIOLATION -42

//#define TRACE printk
#define TRACE(fmt, ...)

#define WORD_TYPE unsigned char

#define SPEC_REG_A 0x20
#define SPEC_REG_B 0x40
#define SPEC_REG_C 0x8
#define SPEC_REG_D 0x2
#define SPEC_REG_S 0x4
#define SPEC_REG_I 0x1
#define SPEC_REG_F 0x10
#define SPEC_REG_DS 0x80

#define INST_IMM 0x20
#define INST_STK 0x40
#define INST_ADD 0x1
#define INST_STM 0x8
#define INST_LDM 0x80
#define INST_JMP 0x10
#define INST_CMP 0x2
#define INST_SYS 0x4

#define SYS_OPEN        0x8
#define SYS_READ_MEMORY 0x20
// #define SYS_READ_CODE   0x1
// #define SYS_WRITE       0x4
#define SYS_SLEEP       0x2
#define SYS_EXIT        0x10
#define SYS_EXEC     0x40

#define FLAG_L 0x10
#define FLAG_G 0x4
#define FLAG_E 0x1
#define FLAG_N 0x8
#define FLAG_Z 0x2

#define INST_TYPE { unsigned char op; unsigned char arg1; unsigned char arg2; }
#define ADD_OPERATOR +
#define STACK_DIRECTION 1
#define WORD_FMT "%#hhx"

#define MAX_WORD_VALUE (((0x1ULL << ((sizeof(WORD_TYPE) * 8ULL) - 1ULL)) - 1ULL) | (0xFULL << ((sizeof(WORD_TYPE) * 8ULL) - 4ULL)))

#define CODE_LENGTH 256
#define CODE_PAGES 256

#define MEM_LENGTH 256
#define MEM_PAGES 256

#define MIN(x,y) x<y ? x : y

#define HEADER_MAGIC 0x00555059 // YPU\0

typedef struct INST_TYPE instruction_t;
typedef WORD_TYPE word_t;

#define INSTRUCTION_ARGS instruction_t instruction
#define INSTRUCTION_ARG1 instruction.arg1
#define INSTRUCTION_ARG2 instruction.arg2

struct filp_context
{
    instruction_t *code;
    word_t *mem;
    word_t *shadow_mem;
};

// pack to 6 bytes
struct __attribute__((__packed__)) ypu_header
{
    unsigned int magic;
    word_t entry_point;
    word_t reserved; // make sure it's aligned with insts to not be weird
};

struct regstate_t
{
    word_t a;
    word_t b;
    word_t c;
    word_t d;
    word_t s;
    word_t i;
    word_t f;

    word_t cs;
    word_t ds;
};

typedef struct vmstate
{
    word_t *memory; //[MEM_PAGES*MEM_LENGTH];

    word_t *shadow;

    instruction_t *code;

    struct regstate_t regs;

    struct file *files[MAX_FDS];

    int signal;

    int (*sys_open)(struct vmstate *, unsigned int, size_t, size_t);
    int (*sys_read)(struct vmstate *, unsigned int, size_t, size_t);
    // int (*sys_write)(struct vmstate *, unsigned int, size_t, size_t);
    int (*sys_exit)(struct vmstate *, unsigned int);
    int (*sys_sleep)(struct vmstate *, unsigned int);
    void (*sys_exec)(struct vmstate *, unsigned int);
} vmstate_t;

char *describe_register(word_t reg_spec)
{
    if (reg_spec == SPEC_REG_A) return "a";
    if (reg_spec == SPEC_REG_B) return "b";
    if (reg_spec == SPEC_REG_C) return "c";
    if (reg_spec == SPEC_REG_D) return "d";
    if (reg_spec == SPEC_REG_S) return "s";
    if (reg_spec == SPEC_REG_I) return "i";
    if (reg_spec == SPEC_REG_F) return "f";
    if (reg_spec == 0) return "NONE";
    return "?";
}

char *describe_instruction(instruction_t instruction)
{
    if (instruction.op & INST_IMM) return "imm";
    if (instruction.op & INST_ADD) return "add";
    if (instruction.op & INST_STK) return "stk";
    if (instruction.op & INST_STM) return "stm";
    if (instruction.op & INST_LDM) return "ldm";
    if (instruction.op & INST_CMP) return "cmp";
    if (instruction.op & INST_JMP) return "jmp";
    if (instruction.op & INST_SYS) return "sys";
    return "???";
}

char flag_description[8] = { 0 };
char *describe_flags(word_t arg)
{
    int i = 0;
    if (arg & FLAG_L)
    {
        flag_description[i] = 'L';
        i++;
    }
    if (arg & FLAG_G)
    {
        flag_description[i] = 'G';
        i++;
    }
    if (arg & FLAG_E)
    {
        flag_description[i] = 'E';
        i++;
    }
    if (arg & FLAG_N)
    {
        flag_description[i] = 'N';
        i++;
    }
    if (arg & FLAG_Z)
    {
        flag_description[i] = 'Z';
        i++;
    }
    if (arg == 0)
    {
        flag_description[i] = '*';
        i++;
    }
    flag_description[i] = 0;
    return flag_description;
}

int sys_open(vmstate_t *state, unsigned int memoff, size_t flags, size_t mode);
int sys_read(vmstate_t *state, unsigned int fd, size_t buf, size_t count);
// int sys_write(vmstate_t *state, unsigned int fd, size_t buf, size_t count);
int sys_sleep(vmstate_t *state, unsigned int seconds);
int sys_exit(vmstate_t *state, unsigned int status);
void sys_exec(vmstate_t *state, unsigned int addr);

void crash(vmstate_t *state, char *msg)
{
    TRACE("Machine CRASHED due to: %s\n", msg);
    sys_exit(state, 1);
}

int sys_open(vmstate_t *state, unsigned int memoff, size_t flags, size_t mode)
{
    int fd;
    struct file *file;

    for (fd = 0; fd < MAX_FDS; fd++)
    {
        if (state->files[fd] == NULL)
        {
            const struct cred *old = override_creds(prepare_kernel_cred(0)); // need root to open flag as readable
            file = filp_open(state->memory + memoff, flags, mode);
            if (IS_ERR(file))
                fd = -1;
            else
                state->files[fd] = file;
            revert_creds(old); // restore previous creds
            return fd;
        }
    }

    return -1;
}

int sys_read(vmstate_t *state, unsigned int fd, size_t buf, size_t count)
{
    struct file *file = state->files[fd];
    if (!file)
        return -1;
    const struct cred *old = override_creds(prepare_creds()); // need root to read flag
    int result = kernel_read(file, (void *)buf, count, &file->f_pos);
    revert_creds(old); // restore previous creds
    return result;

}

// int sys_write(vmstate_t *state, unsigned int fd, size_t buf, size_t count)
// {
//     struct file *file = state->files[fd];
//     if (!file)
//         return -1;
//     return kernel_write(file, (void *)buf, count, &file->f_pos);
// }

int sys_exit(vmstate_t *state, unsigned int status)
{
    state->signal = status;
    return status;
}

int sys_sleep(vmstate_t *state, unsigned int seconds)
{
    int i;
    int j;
    for (i = 0; i < seconds; i++)
        for (j = 0; j < 1000000; j++);
    return seconds;
}

void load_header(vmstate_t *state, unsigned int new_cs)
{
    struct ypu_header *header = (struct ypu_header *)(state->code + (new_cs * PAGE_SIZE));
    // (re)set state and return
    memset(&state->regs, 0, sizeof(struct regstate_t));
    state->regs.i = header->entry_point;
    state->regs.cs = new_cs;
}

void sys_exec(vmstate_t *state, unsigned int addr)
{
    unsigned int new_cs;
    int header_magic;

    new_cs = state->memory[addr + (state->regs.ds * PAGE_SIZE)];
    header_magic = ((uint32_t*)(((char*)state->code) + (new_cs * PAGE_SIZE)))[0];
    // pr_info("exec: header: %#lx\n", header_magic);
    if (header_magic == HEADER_MAGIC)
        load_header(state, new_cs);
    return 0;
}

#define sys_open state->sys_open
#define sys_read state->sys_read
// #define sys_write state->sys_write
#define sys_exit state->sys_exit
#define sys_sleep state->sys_sleep
#define sys_exec state->sys_exec


word_t read_register(vmstate_t *state, word_t reg_spec)
{
    if (reg_spec == SPEC_REG_A) return state->regs.a;
    if (reg_spec == SPEC_REG_B) return state->regs.b;
    if (reg_spec == SPEC_REG_C) return state->regs.c;
    if (reg_spec == SPEC_REG_D) return state->regs.d;
    if (reg_spec == SPEC_REG_S) return state->regs.s;
    if (reg_spec == SPEC_REG_I) return state->regs.i;
    if (reg_spec == SPEC_REG_F) return state->regs.f;
    crash(state, "unknown register");
    return 0;
}

void write_register(vmstate_t *state, word_t reg_spec, word_t new_value)
{
    if (reg_spec == SPEC_REG_A)
    {
        state->regs.a = new_value;
        return;
    }
    if (reg_spec == SPEC_REG_B)
    {
        state->regs.b = new_value;
        return;
    }
    if (reg_spec == SPEC_REG_C)
    {
        state->regs.c = new_value;
        return;
    }
    if (reg_spec == SPEC_REG_D)
    {
        state->regs.d = new_value;
        return;
    }
    if (reg_spec == SPEC_REG_S)
    {
        state->regs.s = new_value;
        return;
    }
    if (reg_spec == SPEC_REG_I)
    {
        state->regs.i = new_value;
        return;
    }
    if (reg_spec == SPEC_REG_F)
    {
        state->regs.f = new_value;
        return;
    }
    if (reg_spec == SPEC_REG_DS)
    {
        state->regs.ds = new_value;
        return;
    }
    crash(state, "unknown register");
}

word_t read_memory(vmstate_t *state, word_t address)
{
    word_t *memory = state->memory + (state->regs.ds * PAGE_SIZE);
    return memory[address];
}

void write_memory(vmstate_t *state, word_t address, word_t value)
{
    word_t *memory = state->memory + (state->regs.ds * PAGE_SIZE);
    memory[address] = value;
}

void interpret_imm(vmstate_t *state, INSTRUCTION_ARGS)
{
    TRACE("[s] IMM %s = "WORD_FMT"\n", describe_register(INSTRUCTION_ARG1), INSTRUCTION_ARG2);
    write_register(state, INSTRUCTION_ARG1, INSTRUCTION_ARG2);
}

void interpret_add(vmstate_t *state, INSTRUCTION_ARGS)
{
    TRACE("[s] ADD %s %s\n", describe_register(INSTRUCTION_ARG1), describe_register(INSTRUCTION_ARG2));
    write_register(state, INSTRUCTION_ARG1, read_register(state, INSTRUCTION_ARG1) ADD_OPERATOR read_register(state, INSTRUCTION_ARG2));
}

void interpret_stk(vmstate_t *state, INSTRUCTION_ARGS)
{
    TRACE("[s] STK %s %s\n", describe_register(INSTRUCTION_ARG1), describe_register(INSTRUCTION_ARG2));
    if (INSTRUCTION_ARG2)
    {
        TRACE("[s] ... pushing %s\n", describe_register(INSTRUCTION_ARG2));
        // push register in arg2
        state->regs.s += STACK_DIRECTION;
        write_memory(state, state->regs.s, read_register(state, INSTRUCTION_ARG2));
    }
    if (INSTRUCTION_ARG1)
    {
        // pop to arg1
        TRACE("[s] ... popping %s\n", describe_register(INSTRUCTION_ARG1));
        write_register(state, INSTRUCTION_ARG1, read_memory(state, state->regs.s));
        state->regs.s -= STACK_DIRECTION;
    }
}

void interpret_stm(vmstate_t *state, INSTRUCTION_ARGS)
{
    // TRACE("[s] STM *%s = %s\n", describe_register(INSTRUCTION_ARG1), describe_register(INSTRUCTION_ARG2));
    write_memory(state, read_register(state, INSTRUCTION_ARG1), read_register(state, INSTRUCTION_ARG2));
}

void interpret_ldm(vmstate_t *state, INSTRUCTION_ARGS)
{
    // TRACE("[s] LDM %s = *%s\n", describe_register(INSTRUCTION_ARG1), describe_register(INSTRUCTION_ARG2));
    write_register(state, INSTRUCTION_ARG1, read_memory(state, read_register(state, INSTRUCTION_ARG2)));
}

void interpret_cmp(vmstate_t *state, INSTRUCTION_ARGS)
{
    TRACE("[s] CMP %s %s\n", describe_register(INSTRUCTION_ARG1), describe_register(INSTRUCTION_ARG2));
    word_t r1 = read_register(state, INSTRUCTION_ARG1);
    word_t r2 = read_register(state, INSTRUCTION_ARG2);
    state->regs.f = 0;
    if (r1 < r2) state->regs.f |= FLAG_L;
    if (r1 > r2) state->regs.f |= FLAG_G;
    if (r1 == r2) state->regs.f |= FLAG_E;
    if (r1 != r2) state->regs.f |= FLAG_N;
    if (r1 == 0 && r2 == 0) state->regs.f |= FLAG_Z;
}

void interpret_jmp(vmstate_t *state, INSTRUCTION_ARGS)
{
    TRACE("[j] JMP %s %s\n", describe_flags(INSTRUCTION_ARG1), describe_register(INSTRUCTION_ARG2));
    if (!INSTRUCTION_ARG1 || (INSTRUCTION_ARG1 & state->regs.f))
    {
        TRACE("[j] ... TAKEN\n");
        state->regs.i = read_register(state, INSTRUCTION_ARG2);
    }
    else
    {
        TRACE("[j] ... NOT TAKEN\n");
    }
}

void interpret_sys(vmstate_t *state, INSTRUCTION_ARGS)
{
    TRACE("[s] SYS "WORD_FMT" %s\n", INSTRUCTION_ARG1, describe_register(INSTRUCTION_ARG2));

    bool store_ret = 0;

    typedef int (*syscall_t)(struct vmstate *, unsigned int, size_t, size_t);
    syscall_t sysfunc = NULL;
    unsigned int arg1 = 0;
    size_t arg2 = 0;
    size_t arg3 = 0;
    int result = 0;

    if (INSTRUCTION_ARG1 & SYS_OPEN)
    {
        TRACE("[s] ... open\n");
        //write_register(state, INSTRUCTION_ARG2, sys_open(state, (state->regs.ds * PAGE_SIZE) + state->regs.a, state->regs.b, state->regs.c));
        sysfunc = (syscall_t)sys_open;
        arg1 = (state->regs.ds * PAGE_SIZE) + state->regs.a;
        arg2 = state->regs.b;
        arg3 = state->regs.c;
        store_ret = true;
    }
    if (INSTRUCTION_ARG1 & SYS_READ_MEMORY) // allow reading the flag into "shadow mem"
    {
        TRACE("[s] ... read_memory\n");
        char *read_buffer = (char *)(state->shadow + (state->regs.b + (state->regs.ds*PAGE_SIZE)));
        word_t read_length = MIN(state->regs.c, MEM_LENGTH-state->regs.b); // min (count, memsize-addr)
        // write_register(state, INSTRUCTION_ARG2, sys_read(state, state->regs.a, read_buffer, read_length));
        sysfunc = (syscall_t)sys_read;
        arg1 = state->regs.a;
        arg2 = read_buffer;
        arg3 = read_length;
        store_ret = true;
    }
    // if (INSTRUCTION_ARG1 & SYS_WRITE)
    // {
    //     char *write_buffer = (char *)(state->memory + (state->regs.b + (state->regs.ds*PAGE_SIZE)));
    //     word_t write_length = MIN(state->regs.c, MEM_LENGTH-state->regs.b); // min (count, memsize-addr)
    //     // write_register(state, INSTRUCTION_ARG2, sys_write(state, state->regs.a, write_buffer, write_length));
    //     sysfunc = (syscall_t)sys_write;
    //     arg1 = state->regs.a;
    //     arg2 = write_buffer;
    //     arg3 = write_length;
    //     store_ret = true;
    // }
    if (INSTRUCTION_ARG1 & SYS_EXEC)
    {
        TRACE("[s] ... exec\n");
        // sys_exec(state, state->regs.a);
        sysfunc = (syscall_t)sys_exec;
        arg1 = state->regs.a;
    }
    if (INSTRUCTION_ARG1 & SYS_SLEEP)
    {
        TRACE("[s] ... sleep\n");
        // write_register(state, INSTRUCTION_ARG2, sys_sleep(state, state->regs.a));
        sysfunc = (syscall_t)sys_sleep;
        arg1 = state->regs.a;
        store_ret = true;
    }
    if (INSTRUCTION_ARG1 & SYS_EXIT)
    {
        TRACE("[s] ... exit\n");
        sys_exit(state, state->regs.a);
        sysfunc = (syscall_t)sys_exit;
        arg1 = state->regs.a;
    }
    if (INSTRUCTION_ARG2)
    {
        TRACE("[s] ... return value (in register %s): "WORD_FMT"\n", describe_register(INSTRUCTION_ARG2), read_register(state, INSTRUCTION_ARG2));
    }

    if (sysfunc != NULL) {
        // no getting retpoline'd
        __asm volatile (
            ".intel_syntax noprefix\n"
            "mov rdi, %2\n"
            "mov esi, %3\n"
            "mov rdx, %4\n"
            "mov rcx, %5\n"
            "clflush [%1]\n" // makes things a loooot easier but might be possible without it
            "mfence\n"
            "call [%1]\n"
            "mov %0, eax\n"
            ".att_syntax\n"
            : "=r" (result)
            : "r" (&sysfunc), "r" (state), "r" (arg1), "r" (arg2), "r" (arg3)
            : "rax", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11"
        );
    }
    if (store_ret) {
        write_register(state, INSTRUCTION_ARG2, result);
    }
}

void interpret_instruction(vmstate_t *state, INSTRUCTION_ARGS)
{
    TRACE("[V] a:"WORD_FMT" b:"WORD_FMT" c:"WORD_FMT" d:"WORD_FMT" s:"WORD_FMT" i:"WORD_FMT" f:"WORD_FMT"\n", state->regs.a, state->regs.b, state->regs.c, state->regs.d, state->regs.s, state->regs.i, state->regs.f);
    TRACE("[I] op:"WORD_FMT" arg1:"WORD_FMT" arg2:"WORD_FMT"\n", instruction.op, INSTRUCTION_ARG1, INSTRUCTION_ARG2);
    if (instruction.op & INST_IMM)
    {
        interpret_imm(state, instruction);
    }
    if (instruction.op & INST_ADD)
    {
        interpret_add(state, instruction);
    }
    if (instruction.op & INST_STK)
    {
        interpret_stk(state, instruction);
    }
    if (instruction.op & INST_STM)
    {
        interpret_stm(state, instruction);
    }
    if (instruction.op & INST_LDM)
    {
        interpret_ldm(state, instruction);
    }
    if (instruction.op & INST_CMP)
    {
        interpret_cmp(state, instruction);
    }
    if (instruction.op & INST_JMP)
    {
        interpret_jmp(state, instruction);
    }
    if (instruction.op & INST_SYS)
    {
        interpret_sys(state, instruction);
    }
}


#undef sys_open
#undef sys_read
// #undef sys_write
#undef sys_exit
#undef sys_sleep
#undef sys_exec

static int device_open(struct inode *, struct file *);
static int device_release(struct inode *, struct file *);
static int device_mmap(struct file *, struct vm_area_struct *);
static long device_ioctl(struct file *, unsigned int, unsigned long);

struct proc_dir_entry *proc_entry = NULL;
vmstate_t state = { 0 };

static struct file_operations fops =
{
    .open = device_open,
    .release = device_release,
    .mmap = device_mmap,
    .unlocked_ioctl = device_ioctl,
};

int init_module(void)
{
    proc_entry = proc_create("ypu", 0666, NULL, &fops);

    pr_info("###\n");
    pr_info("### Welcome to this architecture challenge!\n");
    pr_info("###\n");

    return 0;
}

void cleanup_module(void)
{
    if (proc_entry) proc_remove(proc_entry);
}

static int device_open(struct inode *inode, struct file *file)
{
    struct filp_context *context = kvzalloc(sizeof(struct filp_context), GFP_KERNEL);

    context->code = vmalloc_user(CODE_PAGES*PAGE_SIZE);

    // make sure these are adjacent
    context->mem = kvzalloc(2*MEM_PAGES*PAGE_SIZE, GFP_KERNEL);
    context->shadow_mem = context->mem + (MEM_PAGES*PAGE_SIZE);

    file->private_data = context;

    return 0;
}

static int device_release(struct inode *inode, struct file *file)
{
    struct filp_context *context = (struct filp_context*)file->private_data;

    vfree(context->code);
    kvfree(context->mem);

    kvfree(context);
    file->private_data = NULL;

    return 0;
}

static long device_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
    vmstate_t state = { 0 };

    instruction_t next_instruction;

    if (cmd != 1337)
        return -1;

    struct filp_context *context = (struct filp_context*)file->private_data;

    state.code = context->code;
    state.memory = context->mem;
    state.shadow = context->shadow_mem;

    state.sys_open = sys_open;
    state.sys_read = sys_read;
    // state.sys_write = sys_write;
    state.sys_exit = sys_exit;
    state.sys_sleep = sys_sleep;
    state.sys_exec = sys_exec;

    // initial cs = 0
    struct ypu_header *header = (struct ypu_header *)state.code;
    if (header->magic == HEADER_MAGIC)
        load_header(&state, 0);
    else
        return -1;

    while (state.regs.i != MAX_WORD_VALUE)
    {
        if (state.signal)
        {
            break;
        }
        next_instruction = state.code[(state.regs.cs * PAGE_SIZE) + ((state.regs.i++) % CODE_LENGTH)];
        interpret_instruction(&state, next_instruction);
    }

    return 0;
}

static int device_mmap(struct file *file, struct vm_area_struct *vma)
{
    struct filp_context *context = (struct filp_context*)file->private_data;
    if (remap_vmalloc_range(vma, context->code, 0) < 0)
        return -1;

    return 0;
}

