#define _GNU_SOURCE 1

#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include <assert.h>
#include <libgen.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <sys/signal.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <sys/sendfile.h>
#include <sys/prctl.h>
#include <sys/personality.h>
#include <arpa/inet.h>

void __attribute__((constructor)) disable_aslr(int argc, char **argv, char **envp)
{
    int current_personality = personality(0xffffffff);
    assert(current_personality != -1);
    if ((current_personality & ADDR_NO_RANDOMIZE) == 0)
    {
        assert(personality(current_personality | ADDR_NO_RANDOMIZE) != -1);
        fprintf(stderr, "NOTE: This program can only be launched ONCE. You will need to\nrestart your container to launch this program again.\n");
        chmod("/proc/self/exe", 0755);
        execve("/proc/self/exe", argv, envp);
    }
}

#define HTTP_ERROR(y) "HTTP/1.1 " #y "\n\n"
#define REQUIRE(x, y) if (!(x)) { \
    write(client_fd, HTTP_ERROR(y), sizeof(HTTP_ERROR(y))-1); \
    write(client_fd, HTTP_ERROR(y), sizeof(HTTP_ERROR(y))-1); \
    return; \
  }

void send_file(int client_fd, char *path)
{
    struct response_t
    {
        char *head;
        char content[8192];
    } response = { 0 };
    response.head = response.content;

    int file_fd = open(path, O_RDONLY);
    REQUIRE(file_fd > 2, 404);

    struct stat file_stat;
    fstat(file_fd, &file_stat);

    REQUIRE(S_ISREG(file_stat.st_mode), 400)
    REQUIRE(file_stat.st_size < 8192, 413)

    response.head += sprintf(response.head, "HTTP/1.1 200 OK\nServer: pwnserver/1.3333333333333333333333333333333333.7\nX-Leetness-Level: 9001\nContent-type: ");
    if (!strrchr(path, '.')) response.head += sprintf(response.head, "text/plain\n");
    else if (strcmp(strrchr(path, '.')+1, "html") == 0) response.head += sprintf(response.head, "text/html\n");
    else if (strcmp(strrchr(path, '.')+1, "jpg") == 0) response.head += sprintf(response.head, "image/jpeg\n");
    else if (strcmp(strrchr(path, '.')+1, "png") == 0) response.head += sprintf(response.head, "image/png\n");
    else response.head += sprintf(response.head, "text/plain\n");
    response.head += sprintf(response.head, "Content-Length: %d\n", file_stat.st_size);
    response.head += sprintf(response.head, "\n");
    response.head += read(file_fd, response.head, file_stat.st_size);
    REQUIRE(!strstr(response.content, "pwn.college{"), 403);
    write(client_fd, response.content, response.head-response.content);
    close(file_fd);

}

void handle_connection(int client_fd)
{
    char request[8192] = { 0 };
    char method[8] = { 0 };
    char version[10] = { 0 };
    char path[256] = { 0 };
    char resolved_path[512] = { 0 };

    read(client_fd, request, 1000);
    sscanf(request, "%7s %255s %9s", method, path, version);

    REQUIRE(strcmp(method, "GET") == 0, 501);
    REQUIRE(strcmp(version, "HTTP/1.1") == 0, 400);
    sprintf(resolved_path, "/challenge/files/%s", path);
    send_file(client_fd, resolved_path);
}

int challenge(int argc, char **argv, char **envp)
{
    int server_fd;
    struct sockaddr_in server_addr;
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    int option = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &option, sizeof(option));
    assert(server_fd > 0);
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(80);
    assert(bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) >= 0);
    assert(listen(server_fd, 10) >= 0);

    assert(setresgid(65534, 65534, 65534) == 0);
    assert(setresuid(65534, 65534, 65534) == 0);
    assert(open("/flag", O_RDONLY) < 0);

    // setresuid() disables coredumps (for security reasons). This re-enable them.
    assert(prctl(PR_SET_DUMPABLE, 1) == 0);

    puts("Listening on port 80.");

    while (1)
    {
        struct sockaddr_in client_addr;
        socklen_t client_addr_len = sizeof(client_addr);
        int client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_addr_len);
        handle_connection(client_fd);
        close(client_fd);
    }
}

int main(int argc, char **argv, char **envp)
{
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);

    challenge(argc, argv, envp);

}