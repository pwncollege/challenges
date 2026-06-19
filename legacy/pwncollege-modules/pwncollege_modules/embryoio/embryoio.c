#include <unistd.h>
#include <assert.h>

int main(int argc, char **argv, char **envp)
{
    int i = 0;
    char *new_argv[65535] = { 0 };

    // the checker program
    new_argv[i++] = "{{challenge.checker_path}}";

    // the checker args
    {% for checker_arg in challenge.checker_args %}
    new_argv[i++] = "{{checker_arg}}";
    {% endfor %}
    new_argv[i++] = "--reward";
    new_argv[i++] = "/flag";


    // and the old args
    new_argv[i++] = "--";
    for (int j = 0; j < argc; j++) new_argv[i++] = argv[j];

    assert(i < 65535);

    execve(new_argv[0], new_argv, envp);
}
