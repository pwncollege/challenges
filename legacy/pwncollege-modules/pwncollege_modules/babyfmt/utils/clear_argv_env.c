{% if walkthrough %}
printf("To ensure that you are ROPing, rather than doing other tricks, this\n");
printf("will sanitize all environment variables and arguments and close all file\n");
printf("descriptors > 2,\n");
printf("\n");
{% endif %}

for (int i = 3; i < 10000; i++) close(i);
for (char **a = argv; *a != NULL; a++) memset(*a, 0, strlen(*a));
for (char **a = envp; *a != NULL; a++) memset(*a, 0, strlen(*a));
