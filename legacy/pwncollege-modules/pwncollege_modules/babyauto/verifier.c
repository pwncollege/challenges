#define _GNU_SOURCE
#include <sys/sendfile.h>
#include <sys/wait.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>

char *programs[] = {
	{% for binary in challenge.programs_to_crash %}
	"{{ binary }}",
	{% endfor %}
	NULL
};

char *program_args[] = {
	NULL,
	{% for arg in challenge.program_args %}
	"{{ arg }}",
	{% endfor %}
	NULL
};

int main(int argc, char **argv)
{
	int crashes_needed = {{ challenge.crashes_needed }};
	char program[1024] = { 0 };
	char input[1024] = { 0 };
	int status;
	int i;

	printf("[-] Welcome to %s!\n", argv[0]);       
	puts("[-] This challenge series will teach you how to search for bugs in software");
	puts("[-] on a large scale. The challenge has a list of binaries for you to find");
	puts("[-] crash bugs in. You will need to find crashes in them, create a file with");
	puts("[-] the crashing input, instruct this challenge to execute the binaries with");
	puts("[-] the crashing input. Good luck!");
	puts("");

	{% if walkthrough %}
	puts("[+] We suggest using {{challenge.suggested_method}} to find the bugs!");
	{% endif %}

	puts("[-] Each program will be executed as follows:");
	printf("# /path/to/program ");
	for (int j = 1; program_args[j] != NULL; j++)
		printf("%s ", program_args[j]);
	printf("\n");

	while (crashes_needed)
	{
		puts("");
		puts("[#] CURRENT STATUS");
		for (int i = 0; i < sizeof(programs)/sizeof(char *); i++)
			if (programs[i]) printf("- NOT CRASHED: %s\n", programs[i]);
		printf("- You must crash %d more programs to get the flag.\n", crashes_needed);

		printf("Path to program: ");
		scanf("%1000s", program);
		printf("Path to crashing input file: ");
		scanf("%1000s", input);

		for (i = 0; i < sizeof(programs)/sizeof(char *); i++)
			if (programs[i] && strcmp(programs[i], program) == 0) break;

		if (!programs[i])
		{
			puts("[!] INVALID PROGRAM SPECIFIED!");
			continue;
		}

		if (strstr(input, "flag"))
		{
			puts("[!] INVALID INPUT FILENAME!");
			continue;
		}

		int fd = open(input, O_RDONLY | O_NOFOLLOW);
		if (fd < 0)
		{
			puts("[!] UNABLE TO OPEN CRASHING INPUT FILE.");
			continue;
		}

		printf("[+] Running %s with input %s as UID 1337.\n", program, input);
		int pid = fork();
		if (!pid)
		{
			setgid(1337);
			setresuid(1337, 1337, 1337);

			program_args[0] = programs[i];
			{% if challenge.input_arg_index %}
			program_args[{{challenge.input_arg_index}}] = input;
			{% else %}
			dup2(fd, 0);
			{% endif %}
			execve(programs[i], program_args, NULL);
		}

		waitpid(pid, &status, 0);
		if (WIFSIGNALED(status))
		{
			printf("[*] PWNED! Program terminated with signal %d.\n", WTERMSIG(status));
			crashes_needed--;
			programs[i] = NULL;
		}
	}

	puts("[*] Congratulations! You have pwned your way to the flag!");
	sendfile(1, open("/flag", 0), 0, 1024);
}
