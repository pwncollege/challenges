
#include <unistd.h>
#include <fcntl.h>
#include <assert.h>

void __attribute__((constructor)) flag_seed()
{
  char flag[128] = { 0 };
  int fd = open("/flag", 0);
  assert(fd >= 0);
  assert(read(fd, flag, 128) > 0);
  unsigned int seed = 0;
  for (int i = 0; i < (sizeof(flag) / sizeof(seed)); i++)
    seed ^= ((unsigned int *) flag)[i];
  srand(seed);
  memset(flag, 0, 128);
}
