#include <sys/stat.h>
#include <unistd.h>
#include <signal.h>
#include <string.h>
#include <fcntl.h>
#include <stdio.h>

void handle_crash(int signum)
{
	(void)signum;

	// If the process retained saved root IDs, regain euid/egid before reading /flag.
	setresgid(-1, 0, -1);
	setresuid(-1, 0, -1);

	write(STDOUT_FILENO, "You crashed it! Here is your flag:\n", 35);

	char flag[1024];
	memset(flag, 0, sizeof(flag));
	int fd = open("/flag", O_RDONLY);
	if (fd < 0) {
		write(STDERR_FILENO, "unable to open /flag\n", 21);
		_exit(1);
	}
	ssize_t n = read(fd, flag, sizeof(flag));
	if (n > 0) {
		write(STDOUT_FILENO, flag, (size_t)n);
	}
	close(fd);
	_exit(-11 & 0xff);
}

__attribute__((constructor)) void register_crash_flag_handler()
{
	struct sigaction sa = { 0 };
	sa.sa_handler = handle_crash;

	sigaction(SIGSEGV, &sa, NULL);
	sigaction(SIGILL, &sa, NULL);
	sigaction(SIGBUS, &sa, NULL);
	sigaction(SIGABRT, &sa, NULL);
}
