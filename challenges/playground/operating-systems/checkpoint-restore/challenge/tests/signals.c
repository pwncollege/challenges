#include <assert.h>
#include <err.h>
#include <signal.h>

#include <checkpoint.h>

int main(void)
{
    sigset_t blocked;
    sigemptyset(&blocked);
    sigaddset(&blocked, SIGUSR1);
    assert(sigprocmask(SIG_SETMASK, &blocked, NULL) == 0);

    long generation = checkpoint();
    assert(generation >= 0 && generation <= 2);
    assert(sigprocmask(SIG_SETMASK, NULL, &blocked) == 0);
    assert(sigismember(&blocked, SIGUSR1) == 1);
    assert(sigismember(&blocked, SIGUSR2) == 0);
    if (generation == 2)
        return 0;

    sigemptyset(&blocked);
    sigaddset(&blocked, SIGUSR2);
    assert(sigprocmask(SIG_SETMASK, &blocked, NULL) == 0);
    restore();
    errx(1, "restore returned to its caller");
}
