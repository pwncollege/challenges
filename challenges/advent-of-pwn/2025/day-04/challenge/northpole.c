#define _GNU_SOURCE
#include <bpf/bpf.h>
#include <bpf/libbpf.h>
#include <stdbool.h>
#include <ctype.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <unistd.h>

static volatile sig_atomic_t stop;

static void handle_sigint(int sig)
{
    (void)sig;
    stop = 1;
}

static void broadcast_cheer(void)
{
    DIR *d = opendir("/dev/pts");
    struct dirent *de;
    char path[64];
    char flag[256];
    char banner[512];
    ssize_t n;

    if (!d)
        return;

    int ffd = open("/flag", O_RDONLY | O_CLOEXEC);
    if (ffd >= 0) {
        n = read(ffd, flag, sizeof(flag) - 1);
        if (n >= 0)
            flag[n] = '\0';
        close(ffd);
    } else {
        strcpy(flag, "no-flag\n");
    }

    snprintf(
        banner,
        sizeof(banner),
        "🎅 🎄 🎁 \x1b[1;31mHo Ho Ho\x1b[0m, \x1b[1;32mMerry Christmas!\x1b[0m\n"
        "%s",
        flag);

    while ((de = readdir(d)) != NULL) {
        const char *name = de->d_name;
        size_t len = strlen(name);
        bool all_digits = true;

        if (len == 0 || name[0] == '.')
            continue;
        if (strcmp(name, "ptmx") == 0)
            continue;

        for (size_t i = 0; i < len; i++) {
            if (!isdigit((unsigned char)name[i])) {
                all_digits = false;
                break;
            }
        }
        if (!all_digits)
            continue;

        snprintf(path, sizeof(path), "/dev/pts/%s", name);
        int fd = open(path, O_WRONLY | O_NOCTTY | O_CLOEXEC);
        if (fd < 0)
            continue;
        write(fd, "\x1b[2J\x1b[H", 7);
        write(fd, banner, strlen(banner));
        close(fd);
    }

    closedir(d);
}

int main(void)
{
    struct bpf_object *obj = NULL;
    struct bpf_program *prog = NULL;
    struct bpf_link *link = NULL;
    struct bpf_map *success = NULL;
    int map_fd;
    __u32 key0 = 0;
    int err;
    int should_broadcast = 0;

    libbpf_set_strict_mode(LIBBPF_STRICT_ALL);
    setvbuf(stdout, NULL, _IONBF, 0);

    obj = bpf_object__open_file("/challenge/tracker.bpf.o", NULL);
    if (!obj) {
        fprintf(stderr, "Failed to open BPF object: %s\n", strerror(errno));
        return 1;
    }

    err = bpf_object__load(obj);
    if (err) {
        fprintf(stderr, "Failed to load BPF object: %s\n", strerror(-err));
        goto cleanup;
    }

    prog = bpf_object__find_program_by_name(obj, "handle_do_linkat");
    if (!prog) {
        fprintf(stderr, "Could not find BPF program handle_do_linkat\n");
        goto cleanup;
    }

    link = bpf_program__attach_kprobe(prog, false, "__x64_sys_linkat");
    if (!link) {
        fprintf(stderr, "Failed to attach kprobe __x64_sys_linkat: %s\n", strerror(errno));
        goto cleanup;
    }

    signal(SIGINT, handle_sigint);
    signal(SIGTERM, handle_sigint);

    success = bpf_object__find_map_by_name(obj, "success");
    if (!success) {
        fprintf(stderr, "Failed to find success map\n");
        goto cleanup;
    }
    map_fd = bpf_map__fd(success);

    printf("Attached. Press Ctrl-C to quit.\n");
    fflush(stdout);
    while (!stop) {
        __u32 v = 0;
        if (bpf_map_lookup_elem(map_fd, &key0, &v) == 0 && v != 0) {
            should_broadcast = 1;
            stop = 1;
            break;
        }
        usleep(100000);
    }

    if (should_broadcast)
        broadcast_cheer();

cleanup:
    if (link)
        bpf_link__destroy(link);
    if (obj)
        bpf_object__close(obj);
    return err ? 1 : 0;
}
