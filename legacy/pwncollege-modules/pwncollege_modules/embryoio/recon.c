#include <sys/stat.h>
#include <stdbool.h>
#include <assert.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <libgen.h>
#include <dirent.h>
#include <stdio.h>

#define FD_UNK 0
#define FD_PTS 1
#define FD_PIPE 2
#define FD_FILE 3
#define FD_SOCK 4
#define FD_CLOSED 5

#define MAX_FDS 1024
#define PATH_LEN 1024
#define MAX_PROCS 1024

typedef struct process_t process_t;
struct process_t {
	char path[PATH_LEN];
	char *basename;
	int pid;

	int fd_types[MAX_FDS];
	char fd_paths[MAX_FDS][PATH_LEN];
	process_t *fd_partner_procs[MAX_FDS];
	int fd_partner_fds[MAX_FDS];

	process_t *parent;
};

process_t processes[MAX_PROCS] = { 0 };

struct {
	bool valid;
	int src_addr;
	int src_port;
	int dst_addr;
	int dst_port;
	int inode;
	char name[128];
} tcp[1024] = { 0 };

// how it was launched
bool launched_from_ipython;
bool launched_from_python;
bool launched_from_strace;
bool launched_from_system;
bool launched_from_socat;
bool launched_from_shell;
bool launched_from_gdb;


// laziness
process_t *get_process(int pid)
{
	for (int i = 0; i < MAX_PROCS && processes[i].pid; i++)
	{
		if (processes[i].pid == pid) return &processes[i];
	}
	return NULL;
}

char *find_mirror(char *socket_name)
{
	// identify the src tuple
	int i;
	for (i = 0; tcp[i].valid; i++)
	{
		if (strcmp(tcp[i].name, socket_name) == 0) break;
	}

	if (!tcp[i].valid) return NULL;

	// identify the mirror
	for (int j = 0; tcp[j].valid; j++)
	{
		if (tcp[i].src_port == tcp[j].dst_port && tcp[i].src_addr == tcp[j].dst_addr && tcp[i].dst_port == tcp[j].src_port && tcp[i].dst_addr == tcp[j].dst_addr) return tcp[j].name;
	}

	return NULL;
}

void analyze_partners()
{
	for (int i = 0; i < MAX_PROCS; i++)
	{
		for (int fi = 0; fi < MAX_FDS; fi++)
		{
			char *mirror_name = NULL;
			if (processes[i].fd_types[fi] == FD_SOCK) mirror_name = find_mirror(processes[i].fd_paths[fi]);
			if (processes[i].fd_types[fi] == FD_PIPE) mirror_name = processes[i].fd_paths[fi];
			if (!mirror_name) continue;

			for (int j = 0; j < MAX_PROCS; j++)
			{
				for (int fj = 0; fj < MAX_FDS; fj++)
				{
					if (strcmp(processes[j].fd_paths[fj], mirror_name) == 0)
					{
						if (i == j && fi == fj) continue;

						// prioritize *different* processes, but use the same as a fallback
						if (!processes[i].fd_partner_procs[fi] || i != j)
						{
							processes[i].fd_partner_procs[fi] = &processes[j];
							processes[i].fd_partner_fds[fi] = fj;
						}
					}
				}
			}
		}
	}
}

// insanity

void read_tcp_data()
{
	FILE *net_tcp = fopen("/proc/net/tcp", "rb");
	// skip the header
	fscanf(net_tcp, "%*[^\n]\n");

	int i = 0;
	while (!feof(net_tcp))
	{
		fscanf(
			net_tcp,
			"%*[^:]: %x:%x %x:%x %*x %*x:%*x %*x:%*x %*x %*d %*d %u%*[^\n]\n",
			&tcp[i].src_addr, &tcp[i].src_port, &tcp[i].dst_addr, &tcp[i].dst_port, &tcp[i].inode
		);
		sprintf(tcp[i].name, "socket:[%d]", tcp[i].inode);
		tcp[i].valid = true;
		i++;
	}

	fclose(net_tcp);

	//for (i = 0; tcp[i].valid; i++)
	//	printf("TCP %s: %08x:%04x->%08x:%04x\n", tcp[i].name, tcp[i].src_addr, tcp[i].src_port, tcp[i].dst_addr, tcp[i].dst_port);
}

int get_parent(int pid)
{
	char stat_path[128] = { 0 };
	int ppid = 0;

	snprintf(stat_path, 128, "/proc/%d/stat", pid);
	FILE *stat = fopen(stat_path, "rb");
	if (!stat) return 0;
	fscanf(stat, "%*d %*s %*s %d", &ppid);
	fclose(stat);
	return ppid;
}

void examine_fd(int pid, int fd, int *out_type, char *out_path)
{
	// resolve the path
	struct stat fd_stat;
	char fd_realpath[PATH_LEN];
	char fd_procpath[PATH_LEN];
	snprintf(fd_procpath, 128, "/proc/%d/fd/%d", pid, fd);

	if (access(fd_procpath, F_OK) != 0)
	{
		if (out_type) *out_type = FD_CLOSED;
		return;
	}

	// figure out the path
	realpath(fd_procpath, fd_realpath);

	// figure out the type
	if (strstr(fd_realpath, "/dev/pts/"))
	{
		*out_type = FD_PTS;
		strcpy(out_path, fd_realpath);
	}
	else if (strstr(fd_realpath, "fd/pipe:["))
	{
		*out_type = FD_PIPE;
		strcpy(out_path, basename(fd_realpath));

		// TODO: partner
	}
	else if (strstr(fd_realpath, "fd/socket:["))
	{
		*out_type = FD_SOCK;
		strcpy(out_path, basename(fd_realpath));
		//char *mirror = find_mirror(out_path);
		//if (mirror && out_partner_pid) *out_partner_pid = find_owner(mirror);
	}
	else if (stat(fd_realpath, &fd_stat) == 0 && S_ISREG(fd_stat.st_mode))
	{
		*out_type = FD_FILE;
		strcpy(out_path, fd_realpath);
	}
	else
	{
		*out_type = FD_UNK;
		strcpy(out_path, fd_realpath);
	}
}

void examine_proc(int pid, process_t *p)
{
	p->pid = pid;
	read_tcp_data();

	// recon the FDs
	for (int i = 0; i < MAX_FDS; i++) examine_fd(pid, i, &p->fd_types[i], p->fd_paths[i]);

	// find the path
	char proc_exe_path[128];
	snprintf(proc_exe_path, 128, "/proc/%d/exe", pid);
	realpath(proc_exe_path, p->path);
	p->basename = basename(p->path);
}

void examine_procs()
{
	DIR *dp;
	struct dirent *ep;
	dp = opendir("/proc");
	int i = 0;
	while ((ep = readdir(dp)))
	{
		int pid = atoi(ep->d_name);
		if (!pid) continue;
		examine_proc(pid, &processes[i]);
		assert(i < MAX_PROCS);
		i++;
	}
	closedir(dp);

	// resolve parents
	for (int j = 0; j < MAX_PROCS && processes[j].pid; j++)
	{
		int ppid = get_parent(processes[j].pid);
		if (!ppid) continue;
		processes[j].parent = get_process(ppid);
	}

	// resolve connections
	analyze_partners();
}

void describe_process(process_t *p)
{
	printf("#= PID %d\n", p->pid);
	if (p->parent)
	{
		printf("| ppid: %d\n", p->parent->pid);
		printf("| parent basename: %s\n", p->parent->basename);
		printf("| parent stdin: %d\n", p->parent->fd_types[0]);
	}
	else puts("| origin process");
	printf("| self stdin: %d\n", p->fd_types[0]);
	printf("| self stdout: %d\n", p->fd_types[1]);
	printf("| self stderr: %d\n", p->fd_types[2]);

	for (int i = 0; i < MAX_FDS; i++)
	{
		if (p->fd_types[i] == FD_UNK) printf("| FD %d UNK %s\n", i, p->fd_paths[i]);
		if (p->fd_types[i] == FD_PTS || p->fd_types[i] == FD_FILE) printf("| FD %d path:%s\n", i, p->fd_paths[i]);
		if (p->fd_types[i] == FD_SOCK || p->fd_types[i] == FD_PIPE)
		{
			printf("| FD %d connected to pid %d fd %d\n", i, p->fd_partner_procs[i] ? p->fd_partner_procs[i]->pid : 0, p->fd_partner_fds[i]);
		}
	}
}

int main(int argc, char **argv)
{
	examine_procs();
	int pid = argc == 2 ? atoi(argv[1]) : getpid();
	process_t *p = get_process(pid);
	describe_process(p);

	// do some semantic analysis
	if (0 == strncmp(p->parent->basename, "python", strlen("python"))) launched_from_python = true;
	if (0 == strcmp(p->parent->basename, "strace")) launched_from_strace = true;
	if (0 == strcmp(p->parent->basename, "socat")) launched_from_socat = true;
	if (0 == strcmp(p->parent->basename, "bash") || strcmp(p->parent->basename, "zsh") == 0) launched_from_shell = true;
	if (0 == strcmp(p->parent->basename, "dash")) launched_from_system = true;
	if (0 == strcmp(p->parent->basename, "gdb")) launched_from_gdb = true;

	// check for ipython
	if (launched_from_python && strstr(p->parent->fd_paths[4], ".ipython/profile_default") == 0) launched_from_ipython = true;

	printf("parent is ipython: %d\n", launched_from_ipython);
	printf("parent is python: %d\n", launched_from_python);
	printf("parent is strace: %d\n", launched_from_strace);
	printf("parent is socat: %d\n", launched_from_socat);
	printf("parent is shell launch: %d\n", launched_from_shell);
	printf("parent is system: %d\n", launched_from_system);
	printf("parent is gdb: %d\n", launched_from_gdb);
}
