#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <sys/personality.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>

extern char **environ;

#define FLAG_FD 100

static int looks_like_post_exec(void)
{
    struct stat st;
    return fstat(FLAG_FD, &st) == 0;
}

static int read_flag_into_memfd(void)
{
    int file = open("/flag", O_RDONLY);
    if (file < 0) {
        perror("open /flag");
        return -1;
    }
    int memfd = syscall(SYS_memfd_create, "f", 0);
    if (memfd < 0) {
        perror("memfd_create flag");
        close(file);
        return -1;
    }
    char buf[256];
    ssize_t n;
    while ((n = read(file, buf, sizeof buf)) > 0) {
        if (write(memfd, buf, n) != n) {
            perror("write flag");
            close(file);
            close(memfd);
            return -1;
        }
    }
    close(file);
    lseek(memfd, 0, SEEK_SET);
    if (dup2(memfd, FLAG_FD) < 0) {
        perror("dup2");
        close(memfd);
        return -1;
    }
    close(memfd);
    return 0;
}

static int copy_self_to_memfd(void)
{
    int self = open("/proc/self/exe", O_RDONLY);
    if (self < 0) {
        perror("open /proc/self/exe");
        return -1;
    }
    int memfd = syscall(SYS_memfd_create, "p", 0);
    if (memfd < 0) {
        perror("memfd_create exe");
        close(self);
        return -1;
    }
    char buf[8192];
    ssize_t n;
    while ((n = read(self, buf, sizeof buf)) > 0) {
        if (write(memfd, buf, n) != n) {
            perror("write self");
            close(self);
            close(memfd);
            return -1;
        }
    }
    close(self);
    return memfd;
}

static int do_setup_phase(int argc, char **argv)
{
    /* Stash the flag where the post-exec phase can find it. */
    if (read_flag_into_memfd() < 0)
        return 1;

    /* Ask the kernel to disable ASLR for our next exec. */
    int pers = personality(0xFFFFFFFF);
    if (personality(pers | ADDR_NO_RANDOMIZE) == -1) {
        perror("personality");
        return 1;
    }

    /* Drop the saved-uid so the next exec is a fully-unprivileged process. */
    if (setresuid(getuid(), getuid(), getuid()) < 0) {
        perror("setresuid");
        return 1;
    }

    /* Re-exec from a memfd copy of ourselves: no SUID bit on the source means
     * the kernel won't trigger secureexec, so the personality flag survives. */
    int exe_memfd = copy_self_to_memfd();
    if (exe_memfd < 0)
        return 1;
    char path[64];
    snprintf(path, sizeof path, "/proc/self/fd/%d", exe_memfd);
    execve(path, argv, environ);
    perror("execve");
    return 1;
}

static int do_challenge_phase(int argc, char **argv)
{
    if (argc != 1) {
        fprintf(stderr,
                "I require argc == 1, but you launched me with argc == %d.\n"
                "Run me with no extra arguments.\n",
                argc);
        return 1;
    }

    unsigned long a0 = (unsigned long)argv[0];
    if ((a0 & 0xFFFF) != 0x5390) {
        fprintf(stderr,
                "argv[0] = %p, but I need (argv[0] & 0xFFFF) == 0x5390.\n"
                "(your environment variables sit on the stack and shift argv[0])\n",
                argv[0]);
        return 1;
    }

    char buf[256];
    ssize_t n = read(FLAG_FD, buf, sizeof buf);
    if (n > 0)
        write(1, buf, n);
    close(FLAG_FD);
    return 0;
}

int main(int argc, char **argv)
{
    if (looks_like_post_exec())
        return do_challenge_phase(argc, argv);
    return do_setup_phase(argc, argv);
}
