obj-m := kbfs.o
KERNEL_DIR := /home/kylebot/Desktop/challenges/pwn.college/2024_spring_qq_mod/kernel3

all:
	gcc -o makefs_kbfs  makefs_kbfs.c
	make -C $(KERNEL_DIR) M=$(PWD) modules
	rm *.o *.mod *.order *.symvers *.mod.c .kbfs* .modules.order.cmd .Module.symvers.cmd
	./makefs_kbfs ./disk.iso

clean:
	make -C $(KERNEL_DIR) M=$(PWD) clean
