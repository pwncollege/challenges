#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <x86intrin.h>
#include <time.h>

#define CACHE_HIT_THRESHOLD 160
#define CACHE_LINE_SIZE 1024
#define BUFF_SIZE 256

char buffer[BUFF_SIZE * CACHE_LINE_SIZE];
size_t i;
uint64_t t_no_flush, t_flush;
size_t cache_hit_threshold = CACHE_HIT_THRESHOLD;
int random_index;

void flush(void *p) {
    _mm_clflush(p);
}

uint64_t time_access_no_flush(void *p) {
    uint64_t start, end;
    start = __rdtsc();
    volatile uint64_t x = *(volatile uint64_t*)p;
    _mm_mfence();
    end = __rdtsc();
    return end - start;
}

uint64_t time_access_flush(void *p) {
    uint64_t start, end;
    flush(p);
    _mm_mfence();
    start = __rdtsc();
    volatile uint64_t x = *(volatile uint64_t*)p;
    _mm_mfence();
    end = __rdtsc();
    _mm_sfence();
    return end - start;
}

void victim_function(size_t idx) {
    volatile char x = buffer[idx * CACHE_LINE_SIZE];
}

void flush_cachelines() {
  char * addr;
    for (int j = 0; j < BUFF_SIZE * CACHE_LINE_SIZE; j++) {
      addr = buffer + j;
      flush(addr);
    }
}

void read_to_mem() {
  int index;
  char *addr;
  printf("index: ");
  scanf("%d", &index);
  printf("\n");
  addr = buffer + index * CACHE_LINE_SIZE;
  printf("val: ");
  scanf("%1s", addr);
  printf("\n");
}

void write_from_mem() {
  int index;
  char val;
  char *addr;
  printf("index: ");
  scanf("%d", &index);
  addr = buffer + index * CACHE_LINE_SIZE;

  printf("The value at buffer[%d] is: %c\n", index, addr);
}


void access_random_location() {
  random_index = (rand_r(&random_index) % BUFF_SIZE) ;
  volatile char rand_loc = buffer[random_index * CACHE_LINE_SIZE];
}

void get_flag() {
  int index;
  printf("What index was randomly accessed?\n");
  scanf("%d", &index);

  if (random_index == index) {
    printf("Correct!  Here's your flag!\n");
    sendfile(1, open("/flag", 0), 0, 256);
  }
  else {
    printf("WRONG!\n");
  }
}


time_accesses() {
  int index;
  char * addr;
  for (i = 0; i < BUFF_SIZE; i++) {
    int mix_i = ((i * 167) + 13) & 255;
    index = mix_i * CACHE_LINE_SIZE;
    addr = buffer + index;
    t_no_flush = time_access_no_flush(addr);
    printf("index %lu accessed in %lu cycles\n", mix_i, t_no_flush);
  }
}

void menu() {
  char input[256];

  while(1) {
    printf("flush_cachelines / read_to_mem / write_from_mem / time_accesses / access_random / get_flag / quit\n");

    scanf("%255s", input);

    if (strstr(input, "flush_cachelines")) {
      flush_cachelines();
    }
    else if (strstr(input, "read_to_mem")) {
      read_to_mem();
    }
    else if(strstr(input, "write_from_mem")) {
      write_from_mem();
    }
    else if(strstr(input, "access_random")) {
      access_random_location();
    }
    else if(strstr(input, "get_flag")) {
      get_flag();
    }
    else if(strstr(input, "time_accesses")) {
      time_accesses();
    }
    else if(strstr(input, "quit")) {
      exit(0);
    }
  }
}

int main() {
  int t = (int) time(NULL);
  random_index = rand_r(&t);
  menu();
  return 0;
}

