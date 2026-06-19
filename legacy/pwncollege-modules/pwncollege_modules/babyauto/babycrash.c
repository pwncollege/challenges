#include <unistd.h>
#include <string.h>
#include <stdio.h>

{% if challenge.solution_string %};
char *SOLUTION = "{{challenge.solution_string}}";
{% endif %}

int main()
{
    puts("Input:");

    {% if challenge.solution_string %}
      char buffer[32] = { 0 };
      scanf("%30s", buffer);
      if (strcmp(SOLUTION, buffer) == 0)
    {% elif challenge.solution_num %}
      {{challenge.solution_type}} num;
      scanf("%llu", &num);
      {% for offset in challenge.solution_offsets %}
      num += {{offset}};
      {% endfor %}
      if ({{challenge.solution_num}} == num)
    {% endif %}
    {
        puts("Success. Crashing!");
    	int *crasher = NULL;
    	*crasher = 0;
    }
    else
    {
        puts("Failure!");
    }
}
