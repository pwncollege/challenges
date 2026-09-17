#ifndef CHECKPOINT_H
#define CHECKPOINT_H

#include <unistd.h>

#define SYS_checkpoint 470
#define SYS_restore 471

static inline long checkpoint(void)
{
    return syscall(SYS_checkpoint);
}

static inline long restore(void)
{
    return syscall(SYS_restore);
}

#endif
