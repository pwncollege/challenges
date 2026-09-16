#include <errno.h>
#include <stdio.h>
#include <unistd.h>

#define SYS_hello 470

int main(int argc, char **argv)
{
    for (int i = 1; i < argc; i++) {
        if (syscall(SYS_hello, argv[i]) == -1 && errno == ENOSYS) {
            perror("hello");
            return ENOSYS;
        }
    }

    return 0;
}
