
#define FLAG_BUFF_SZ 256

char flag_val[FLAG_BUFF_SZ];

void read_flag_to_global() {
  int fd = open("/flag", O_RDONLY);

  int n = read(fd, flag_val, FLAG_BUFF_SZ);
  if (!fd || n <= 0) {
    printf("Failed to read flag file.  Exiting");
    exit(1);
  }
  close(fd);
}

// The real code does some inject synchronizaiton garbage
// not worth outputing to the user.  This is the same
// for all intensive purposes.
void print_fake_init() {
  puts("// Shared memory will start with a semaphore");
  puts("// that allows hacker program to trigger behavior");
  puts("sem_t *sem = (sem_t *) shared_memory_base;");
  puts("sem_init(sem, 1, 0);");
  puts(" ");
  puts("// Followed by a flag access index.");
  puts("int *index = (int *) (sem + 1);");
  puts("*index = 0;");
  puts(" ");
}
