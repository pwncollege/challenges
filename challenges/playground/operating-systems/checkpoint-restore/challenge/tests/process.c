#include <assert.h>
#include <err.h>
#include <string.h>
#include <sys/stat.h>

#include <checkpoint.h>

int main(void)
{
    assert(mkdir("/tmp/jail", 0755) == 0);
    assert(chdir("/tmp") == 0);
    umask(0027);

    long generation = checkpoint();
    assert(generation >= 0);
    if (generation == 0) {
        assert(chroot("/tmp/jail") == 0);
        assert(chdir("/") == 0);
        umask(0077);
        restore();
        errx(1, "restore returned to its caller");
    }

    char cwd[64];
    assert(generation == 1);
    assert(getcwd(cwd, sizeof(cwd)) && strcmp(cwd, "/tmp") == 0);
    assert(access("/bin/busybox", X_OK) == 0);
    assert(umask(0027) == 0027);
    return 0;
}
