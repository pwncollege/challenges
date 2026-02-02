#include <stdio.h>
#include <stdlib.h>

int main(void) {
    FILE *f = fopen("/flag", "r");
    if (!f) {
        perror("fopen");
        return 1;
    }
    char buf[4096];
    size_t n = fread(buf, 1, sizeof(buf), f);
    fclose(f);
    fwrite(buf, 1, n, stdout);
    return 0;
}
