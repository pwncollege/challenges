#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/mount.h>
#include <sys/ioctl.h>
#include <linux/loop.h>

char loop_device_path[64];

void check_valid_disk(char *path)
{
	struct stat statbuf;
	char buf[5];
	memset(buf, 0, sizeof(buf));

	if (stat(path, &statbuf)) {
		printf("fail to stat %s!\n", path);
		exit(-1);
	}

	if ((statbuf.st_mode & S_IFMT) != S_IFREG) {
		printf("%s is not a regular file!\n", path);
		exit(-1);
	}

	 int ret = access(path, R_OK | W_OK);
	 if (ret) {
		 printf("%s is not readable or not writable!\n", path);
		 exit(-1);
	 }

	 int fd = open(path, O_RDWR);
	 if (fd <= 0) {
		 printf("fail to open %s\n", path);
		 exit(-1);
	 }
	 ret = read(fd, buf, 4);
	 if (ret != 4) {
		 printf("fail to read %s\n", path);
		 exit(-1);
	 }
	 if(strncmp(buf, "KBFS", 4)) {
		 printf("%s it not a KBFS image!\n", path);
		 exit(-1);
	 }
}

void check_valid_mnt_path(char *path)
{
	struct stat statbuf;

	if (stat(path, &statbuf)) {
		printf("fail to stat %s!\n", path);
		exit(-1);
	}

	if ((statbuf.st_mode & S_IFMT) != S_IFDIR) {
		printf("%#x", (statbuf.st_mode & S_IFMT));
		printf("%s is not a directory!\n", path);
		exit(-1);
	}
}

void mount_loop_device(char *dpath)
{
	int fd = open(dpath, O_RDWR);
	if (fd < 0) {
		printf("fail to open %s\n", dpath);
		exit(-1);
	}

	int loop_control_fd = open("/dev/loop-control", O_RDWR);
	if (loop_control_fd < 0) {
		puts("Failed to open /dev/loop-control");
		exit(-1);
	}
	
	int loop_device_number = ioctl(loop_control_fd, LOOP_CTL_GET_FREE);
	if (loop_device_number < 0) {
		puts("Failed to get free loop device");
		exit(-1);
	}
	
	snprintf(loop_device_path, sizeof(loop_device_path), "/dev/loop%d", loop_device_number);
	
	int loop_fd = open(loop_device_path, O_RDWR);
	if (loop_fd < 0) {
		puts("Failed to open loop device");
		exit(-1);
	}
	
	if (ioctl(loop_fd, LOOP_SET_FD, fd) < 0) {
		puts("Failed to set loop device");
		exit(-1);
	}
	
	close(loop_control_fd);

	char buf[5];
	memset(buf, 0, sizeof(buf));
	read(loop_fd, buf, 4);

	if (strncmp(buf, "KBFS", 4)) {
		puts("hmmm, fishy. are you trying to race with me?");
		exit(-1);
	}
}

void do_mount(char *mnt_path)
{
	int ret = mount(loop_device_path, mnt_path, "kbfs", 0, NULL);
	printf("mount ret: %d\n", ret);
	if (ret) {
		puts("fail to mount the file system...");
		exit(-1);
	}
}

void print_flag()
{
	int fd = open("/flag", O_RDONLY);
	char buffer[0x100];
	memset(buffer, 0, sizeof(buffer));
	read(fd, buffer, sizeof(buffer));
	puts(buffer);
}

int main(int argc, char *argv[])
{
	if (argc < 3) {
		printf("usage: %s <disk> <mount_point>\n", argv[0]);
		exit(-1);
	}
	
	char *dpath = argv[1];
	char *mnt_path = argv[2];
	check_valid_disk(dpath);
	check_valid_mnt_path(mnt_path);

	mount_loop_device(dpath);
	do_mount(mnt_path);
	print_flag();
}
