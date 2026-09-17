#define _GNU_SOURCE
#include <assert.h>
#include <err.h>
#include <errno.h>
#include <grp.h>

#include <checkpoint.h>

int main(void)
{
    gid_t groups[] = { 17, 42 };
    assert(setgroups(2, groups) == 0);

    long generation = checkpoint();
    assert(generation >= 0 && generation <= 2);
    uid_t real_uid, effective_uid, saved_uid;
    gid_t real_gid, effective_gid, saved_gid;
    assert(getresuid(&real_uid, &effective_uid, &saved_uid) == 0);
    assert(getresgid(&real_gid, &effective_gid, &saved_gid) == 0);
    assert(real_uid == 0 && effective_uid == 0 && saved_uid == 0);
    assert(real_gid == 0 && effective_gid == 0 && saved_gid == 0);
    assert(getgroups(2, groups) == 2 && groups[0] == 17 && groups[1] == 42);
    if (generation == 2)
        return 0;

    assert(setgroups(0, NULL) == 0);
    assert(setgid(1000) == 0);
    assert(setuid(1000) == 0);
    assert(setuid(0) == -1 && errno == EPERM);
    restore();
    errx(1, "restore returned to its caller");
}
