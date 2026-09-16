ifneq ($(KERNELRELEASE),)
obj-m := flag.o
else
.PHONY: all modules modules_install clean

all: modules_install

modules_install: modules

modules modules_install clean:
	$(MAKE) -C /usr/src/linux M=$(CURDIR) INSTALL_MOD_PATH=/usr/src/initramfs $@
endif
