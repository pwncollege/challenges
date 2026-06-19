// should be suid root and -no-pie

#include <fcntl.h>

char flag[128];

int main() {
    int fd = open("/flag", O_RDONLY);
    read(fd, flag, 128);    
    close();

    volatile char c;
    while (1) { 
        for ( int i = 0; i < 128; i++) {
            c = flag[i];
        }
    };
}
