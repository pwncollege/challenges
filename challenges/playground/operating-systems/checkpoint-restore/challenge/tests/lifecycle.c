#include <assert.h>
#include <err.h>
#include <errno.h>
#include <sys/wait.h>

#include <checkpoint.h>

int main(int argc, char **argv)
{
    assert(restore() == -1 && errno == ENOENT);
    if (argc > 1)
        return 0;

    long generation = checkpoint();
    assert(generation >= 0 && generation <= 1);
    if (generation == 0) {
        execl("/no-such-program", "missing", NULL);
        assert(errno == ENOENT);
        pid_t child = fork();
        assert(child >= 0);
        if (child == 0) {
            assert(restore() == -1 && errno == ENOENT);
            assert(checkpoint() == 0);
            _exit(17);
        }
        restore();
        errx(1, "restore returned to its caller");
    }

    int status;
    assert(wait(&status) > 0);
    assert(WIFEXITED(status) && WEXITSTATUS(status) == 17);
    execl(argv[0], argv[0], "exec", NULL);
    err(1, "exec");
}
