#include <windows.h>

#define BUFFER_SIZE 0x1000
#define FLAG_LEN 56

void challenge();
{% if challenge.shellcode_runner %}
  void execute_shellcode();
{% endif %}


{% if challenge.win_func or challenge.leak_flag_addr or challenge.read_flag %}
  char flag_buffer[0x100];
  char *FLAG_PATH = TEXT("C:/flag");
{% endif %}

{% if challenge.windll %}
  HMODULE hMod;
{% endif %}

HANDLE hStdin;
HANDLE hStdout;
char message[BUFFER_SIZE];

{% if challenge.win_func %}
void win() {
	char buffer[256];
	DWORD wat;
	LPDWORD bytes_read = &wat;

	HANDLE hFile = CreateFile(FLAG_PATH, GENERIC_READ, FILE_SHARE_READ, NULL,
			OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL | FILE_ATTRIBUTE_READONLY, NULL);

	if (hFile == INVALID_HANDLE_VALUE) {
		printf("Failed to open flag!");
		return;
	}

	if (FALSE == ReadFile(hFile, buffer, FLAG_LEN, bytes_read, NULL)) {
		puts("Failed to read!");
	}

	else {
	  DWORD to_write = strlen(buffer);
	  WriteFile(hStdout, buffer, to_write, NULL, NULL);
	}
}
{% endif %}

{% if challenge.shellcode_runner %}
void execute_shellcode() {
	CHAR buffer[BUFFER_SIZE];
	DWORD toRead = BUFFER_SIZE;
	DWORD actuallyRead = 0;
	void (*fn)() = (void (*)(void)) buffer;

	snprintf(message, BUFFER_SIZE, "Ready to receive shellcode!\n\n");
	WriteFile(hStdout, message, strlen(message), NULL, NULL);
	FlushFileBuffers(hStdout);

	ReadFile(hStdin, buffer, toRead, &actuallyRead, NULL);

	DWORD oldProt;
	PDWORD lpOldProt = &oldProt;
	VirtualProtect(buffer, BUFFER_SIZE, PAGE_EXECUTE_READWRITE, lpOldProt);

	fn();
}
{% endif %}

void challenge() {
	char buffer[{{challenge.bof_buf_sz}}];
	DWORD toRead = 0x600;
	DWORD actuallyRead = 0;

	{% if challenge.leak_win %}
	  void (*win_addr)();
	  {% if challenge.windll %}
	    win_addr = (void (*)(void)) GetProcAddress(hMod, "win");
	  {% else %}
	    win_addr = win;
	  {% endif %}
	{% endif %}

	// Pre-Input Actions
	{% if challenge.read_flag %}
	int bytesRead;

	HANDLE hFlag = CreateFile(FLAG_PATH, GENERIC_READ, FILE_SHARE_READ, NULL,
			OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL | FILE_ATTRIBUTE_READONLY, NULL);
	if (hFlag == INVALID_HANDLE_VALUE) {
		puts("Failed to open Flag file!");
	}

	if (FALSE == ReadFile(hFlag, flag_buffer, FLAG_LEN, &bytesRead, NULL)) {
		puts("Failed to read flag file!");
	}

	{% endif %}

	// Intro blurb
	{% if challenge.intro_text %}
	  snprintf(message, BUFFER_SIZE, "{{ challenge.intro_text }}");
	  WriteFile(hStdout, message, strlen(message), NULL, NULL);
	{% endif %}

	// Leaks
	{% if challenge.leak_flag_addr %}
	  snprintf(message, BUFFER_SIZE, "The Flag has been read into address: 0x%llx\n", flag_buffer);
	  WriteFile(hStdout, message, strlen(message), NULL, NULL);
	{% endif %}

	{% if challenge.leak_win %}
	  snprintf(message, BUFFER_SIZE, "win() is located at: 0x%llx\n", win_addr);
	  WriteFile(hStdout, message, strlen(message), NULL, NULL);
	{% endif %}

	{% if challenge.leak_WriteFile %}
	  snprintf(message, BUFFER_SIZE, "Kernel32!WriteFile addr: 0x%llx\n", WriteFile);
	  WriteFile(hStdout, message, strlen(message), NULL, NULL);
	{% endif %}

	{% if challenge.leak_stdout %}
	  snprintf(message, BUFFER_SIZE,"stdout handle value: 0x%llx\n", hStdout);
	  WriteFile(hStdout, message, strlen(message), NULL, NULL);
	{% endif %}



	// Take User Input
	{% if challenge.smoketest or challenge.shellcode_runner %}
	  // No User input taken
	{% else %}
	  ReadFile(hStdin, buffer, toRead, &actuallyRead, NULL);
	  buffer[actuallyRead] = 0x00;
	{% endif %}

	// End action
	{% if challenge.shellcode_runner %} 
	  execute_shellcode();
	{% endif %}

	{% if challenge.smoketest %}
	  win();
	{% endif %}
}

int main(int argc, char** argv) {
	hStdin = GetStdHandle(STD_INPUT_HANDLE);
	hStdout = GetStdHandle(STD_OUTPUT_HANDLE);
	setvbuf(stdout, NULL, _IONBF, 0);
	setvbuf(stdin, NULL, _IONBF, 0);
	setvbuf(stderr, NULL, _IONBF, 0);

	{% if challenge.windll %}
	  hMod = LoadLibraryA("win.dll");
	{% endif %}

	challenge();
}
