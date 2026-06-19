#include <windows.h>
#include <stdio.h>

#define FLAG_LEN 80

extern __declspec(dllexport) void win();

void win() {
	char *FLAG_PATH = "C:/flag";
	char buffer[256];
	DWORD wat;
	LPDWORD bytes_read = &wat;

	HANDLE hFile = CreateFile(FLAG_PATH, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING,
	  FILE_ATTRIBUTE_NORMAL | FILE_ATTRIBUTE_READONLY, NULL);
	if (hFile == INVALID_HANDLE_VALUE) {
		printf("Failed to open flag!");
		return;
	}

	if (FALSE == ReadFile(hFile, buffer, FLAG_LEN, bytes_read, NULL)) {
		puts("Failed to read!");
	}

	else {
	  DWORD to_write = strlen(buffer);
	  HANDLE hStdout = GetStdHandle(STD_OUTPUT_HANDLE);
	  WriteFile(hStdout, buffer,to_write, NULL, NULL);
	}
}
