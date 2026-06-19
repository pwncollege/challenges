
#include <sys/types.h>
#include <unistd.h>

int drop_privs() {
  if (setgid(1000)) {
    perror("setgid(1000)");
    return 1;
  }
  if (setuid(1000)) {
    perror("setuid(1000)");
    return 1;
  }
  return 0;
}
