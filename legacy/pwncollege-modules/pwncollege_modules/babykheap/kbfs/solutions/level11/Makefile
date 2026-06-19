all:
	nasm -f elf64 -o bin.o bin.S
	ld -m elf_x86_64 -s -o bin bin.o
