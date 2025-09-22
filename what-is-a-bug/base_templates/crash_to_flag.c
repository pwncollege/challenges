#include <sys/stat.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <stdio.h>

void handle_crash(int signum)
{
	puts("You crashed it! Here is your flag:");
	char flag[1024] = {0};
	int fd = open("/flag", O_RDONLY);
	if (fd < 0)
	{
		perror("unable to open /flag");
		exit(1);
	}
	read(fd, flag, 1024);
	puts(flag);
	chmod("/flag", 0644);
	close(fd);
	exit(-11 & 0xff);
}

__attribute__((constructor)) void register_crash_flag_handler()
{
	stack_t ss;
	ss.ss_sp = malloc(SIGSTKSZ);
	ss.ss_size = SIGSTKSZ;
	ss.ss_flags = 0;
	if (sigaltstack(&ss, NULL) == -1) {
		perror("sigaltstack");
		exit(1);
	}

	struct sigaction sa = { 0 };
	sa.sa_handler = handle_crash;
	sa.sa_flags = SA_ONSTACK;

	sigaction(SIGSEGV, &sa, NULL);
	sigaction(SIGILL, &sa, NULL);
	sigaction(SIGBUS, &sa, NULL);
}
