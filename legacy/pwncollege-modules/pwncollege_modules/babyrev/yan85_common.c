#define WORD_TYPE {{ challenge.word_type }}

{% if challenge.rerandomize %}
  {% include "babyrev/yan85_rerandomized.c" %}
{% else %}
  {% include "babyrev/yan85_prerandomized.c" %}
{% endif %}

#define ADD_OPERATOR +
#define STACK_DIRECTION 1
#define WORD_FMT "%#hhx"

#define MAX_WORD_VALUE (((0x1ULL << ((sizeof(WORD_TYPE) * 8ULL) - 1ULL)) - 1ULL) | (0xFULL << ((sizeof(WORD_TYPE) * 8ULL) - 4ULL)))
#define CODE_LENGTH 256
#define MEM_LENGTH {{challenge.memory_size}}
#define MIN(x,y) x<y ? x : y

typedef struct INST_TYPE instruction_t;
typedef WORD_TYPE word_t;

struct regstate_t {
  word_t a;
  word_t b;
  word_t c;
  word_t d;
  word_t s;
  word_t i;
  word_t f;
};

typedef struct {% if challenge.packed_state %} __attribute__((__packed__)) {% endif %} vmstate {
  {% if challenge.direct_interpret_calls %}
    word_t memory[MEM_LENGTH];
  {% elif challenge.remote_code %}
    word_t memory[MEM_LENGTH];
    instruction_t *code;
  {% else %}
    {% if challenge.mem_first %}
      word_t memory[MEM_LENGTH];
      instruction_t code[CODE_LENGTH];
    {% else %}
      instruction_t code[CODE_LENGTH];
      word_t memory[MEM_LENGTH];
    {% endif %}
  {% endif %}

  {% if challenge.compiled %}
    void *compiled_code;
    unsigned long long instruction_offsets[CODE_LENGTH];
  {% else %}
    struct regstate_t regs;
  {% endif %}

  {{ yan85_extra_vmstate_fields }}
} vmstate_t;

int sys_open(vmstate_t *state, char *pathname, int flags, int mode);
int sys_read(vmstate_t *state, int fd, void *buf, size_t count);
int sys_write(vmstate_t *state, int fd, void *buf, size_t count);
int sys_sleep(vmstate_t *state, int seconds);
int sys_exit(vmstate_t *state, int status);

void crash(vmstate_t *state, char *msg)
{
  TRACE("Machine CRASHED due to: %s\n", msg);
  sys_exit(state, 1);
}
