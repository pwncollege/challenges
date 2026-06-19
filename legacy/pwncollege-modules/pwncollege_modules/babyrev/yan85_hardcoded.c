{% set input_location = challenge.key_location-32 %}

// read
{% if challenge.c_read %}
read(0, &state->memory[{{input_location}}], {{ challenge.input_solution.__len__() }});
{% else %}
interpret_imm(state, SPEC_REG_B, {{input_location}});
interpret_imm(state, SPEC_REG_C, {{ challenge.input_solution.__len__() }});
interpret_imm(state, SPEC_REG_A, 0);
interpret_sys(state, SYS_READ_MEMORY, SPEC_REG_A);
{% endif %}

// stored desired value into memory
{% if challenge.c_expected %}
{% for key_char in challenge.input_solution %}
state->memory[{{ challenge.key_location + loop.index - 1 }}] = {{ key_char }};
{% endfor %}
{% else %}
interpret_imm(state, SPEC_REG_B, {{challenge.key_location}});
interpret_imm(state, SPEC_REG_C, 1);
{% for key_char in challenge.input_solution %}
	interpret_imm(state, SPEC_REG_A, {{key_char}});
	interpret_stm(state, SPEC_REG_B, SPEC_REG_A);
	interpret_add(state, SPEC_REG_B, SPEC_REG_C);
{% endfor %}
{% endif %}

// mangle
{% if challenge.manglers and not challenge.mangle_memcmp %}
interpret_imm(state, SPEC_REG_B, {{challenge.key_location if challenge.mangle_key else input_location}});
interpret_imm(state, SPEC_REG_C, 1);
{% for diff_char in challenge.key_differences %}
	interpret_ldm(state, SPEC_REG_A, SPEC_REG_B);
	interpret_imm(state, SPEC_REG_D, {{diff_char}});
	interpret_add(state, SPEC_REG_A, SPEC_REG_D);
	interpret_stm(state, SPEC_REG_B, SPEC_REG_A);
	interpret_add(state, SPEC_REG_B, SPEC_REG_C);
{% endfor %}
{% endif %}

// memcmp
{% if challenge.c_memcmp %}
int match = memcmp(&state->memory[{{challenge.key_location}}], &state->memory[{{input_location}}], {{challenge.input_solution.__len__()}}) == 0;
{% else %}
int match = 1;
{% for key_char in challenge.input_solution %}
	interpret_imm(state, SPEC_REG_B, {{challenge.key_location+loop.index-1}});
	interpret_ldm(state, SPEC_REG_B, SPEC_REG_B);
	{% if challenge.manglers and challenge.mangle_memcmp and challenge.mangle_key %}
	interpret_imm(state, SPEC_REG_C, {{challenge.key_differences[loop.index-1]}});
	interpret_add(state, SPEC_REG_B, SPEC_REG_C);
	{% endif %}
	interpret_imm(state, SPEC_REG_A, {{input_location+loop.index-1}});
	interpret_ldm(state, SPEC_REG_A, SPEC_REG_A);
	{% if challenge.manglers and challenge.mangle_memcmp and not challenge.mangle_key %}
	interpret_imm(state, SPEC_REG_C, {{challenge.key_differences[loop.index-1]}});
	interpret_add(state, SPEC_REG_A, SPEC_REG_C);
	{% endif %}
	interpret_cmp(state, SPEC_REG_A, SPEC_REG_B);

	if (!(state->regs.f & FLAG_E)) match = 0;
{% endfor %}
{% endif %}

// victory
{% if challenge.c_success %}
if (match)
{
	char buf[128];
	printf("CORRECT! Your flag: ");
	write(1, buf, read(open("/flag", O_RDONLY), buf, 100));
}
else
{
	printf("INCORRECT!");
}
{% else %}
interpret_imm(state, SPEC_REG_A, 1);
interpret_imm(state, SPEC_REG_B, 0);
interpret_imm(state, SPEC_REG_C, 1);
if (match)
{
	{% for c in "CORRECT! Your flag:" %}
	interpret_imm(state, SPEC_REG_D, '{{c}}');
	interpret_stm(state, SPEC_REG_B, SPEC_REG_D);
	interpret_sys(state, SYS_WRITE, SPEC_REG_A);
	{% endfor %}
	interpret_imm(state, SPEC_REG_D, '\n');
	interpret_stm(state, SPEC_REG_B, SPEC_REG_D);
	interpret_sys(state, SYS_WRITE, SPEC_REG_A);

	// open flag...
	{% for c in "/flag" %}
	interpret_imm(state, SPEC_REG_D, '{{c}}');
	interpret_imm(state, SPEC_REG_B, {{loop.index-1}});
	interpret_stm(state, SPEC_REG_B, SPEC_REG_D);
	{% endfor %}
	interpret_imm(state, SPEC_REG_D, 0);
	interpret_imm(state, SPEC_REG_B, 5);
	interpret_stm(state, SPEC_REG_B, SPEC_REG_D);
	interpret_imm(state, SPEC_REG_A, 0);
	interpret_imm(state, SPEC_REG_B, 0);
	interpret_sys(state, SYS_OPEN, SPEC_REG_A);

	// read flag...
	interpret_imm(state, SPEC_REG_C, 100);
	interpret_sys(state, SYS_READ_MEMORY, SPEC_REG_C);

	// write flag...
	interpret_imm(state, SPEC_REG_A, 1);
	interpret_sys(state, SYS_WRITE, SPEC_REG_C);

	interpret_imm(state, SPEC_REG_A, 0);
}
else
{
	{% for c in "INCORRECT!" %}
	interpret_imm(state, SPEC_REG_D, '{{c}}');
	interpret_stm(state, SPEC_REG_B, SPEC_REG_D);
	interpret_sys(state, SYS_WRITE, SPEC_REG_A);
	{% endfor %}

	interpret_imm(state, SPEC_REG_A, 1);
}
{% endif %}

{% if challenge.c_exit %}
exit(match ? 0 : 1);
{% else %}
interpret_imm(state, SPEC_REG_D, '\n');
interpret_stm(state, SPEC_REG_B, SPEC_REG_D);
interpret_sys(state, SYS_WRITE, SPEC_REG_A);
interpret_sys(state, SYS_EXIT, SPEC_REG_A);
{% endif %}
