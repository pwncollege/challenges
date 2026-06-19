
void *heap_mapping_addr = NULL;
void *main_thread_tcache = NULL;
__attribute__((constructor)) void get_heap_location()
{
    heap_mapping_addr = sbrk(0);
    malloc(0); // Initialize tcache
    main_thread_tcache = heap_mapping_addr + 0x10;
}

typedef struct tcache_entry {
    struct tcache_entry *next;
    /* This field exists to detect double frees.  */
    struct tcache_perthread_struct *key;
} tcache_entry;

#define TCACHE_MAX_BINS 64
typedef struct tcache_perthread_struct {
    uint16_t counts[TCACHE_MAX_BINS];
    tcache_entry *entries[TCACHE_MAX_BINS];
} tcache_perthread_struct;

struct malloc_chunk {
    // Size of previous chunk (if free).
    unsigned long mchunk_prev_size;
    // Size in bytes, including overhead.
    unsigned long mchunk_size;

    // THE CONTENT STARTS HERE IF NOT FREE
    union {
        struct tcache_entry tcache;
        struct {
            struct malloc_chunk* fd;
        } fast;
        struct {
            struct malloc_chunk* fd;
            struct malloc_chunk* bk;
        } small;
        struct {
            struct malloc_chunk* fd;
            struct malloc_chunk* bk;
        } unsorted;
        struct {
            struct malloc_chunk* fd;
            struct malloc_chunk* bk;
            struct malloc_chunk* fd_nextsize;
            struct malloc_chunk* bk_nextsize;
        } large;
        unsigned char content[24];
    };
};

#define CHUNKOF(x) ((struct malloc_chunk *)((char *)x - 16))

char *flag_string(unsigned long flag)
{
    // NON_MAIN_ARENA | IS_MAPPED | PREV_INUSE
    switch (flag & 7) {
    case 0b111:
        return "A|M|P";
    case 0b110:
        return "A|M";
    case 0b101:
        return "A|P";
    case 0b100:
        return "A";
    case 0b011:
        return "M|P";
    case 0b010:
        return "M";
    case 0b001:
        return "P";
    case 0:
        return "NONE";
    }
}

int is_mapped(void *addr)
{
    unsigned char vec[64];
    int result = mincore((void *)((uintptr_t) addr & ~0xfff), 64, vec);
    return !(result < 0 && errno == ENOMEM);
}

void print_chunk(struct malloc_chunk *chunk, void *tcache_key)
{
    char address[20];
    char prev_size[20] = "???";
    char size[29] = "???";
    char next[20] = "???";
    char key[20] = "???";

    snprintf(address, sizeof(address), "%p", chunk->content);

    if (is_mapped(chunk)) {
        snprintf(prev_size, sizeof(prev_size), "%#lx", chunk->mchunk_prev_size);
        snprintf(size, sizeof(size), "%#lx (%s)", chunk->mchunk_size, flag_string(chunk->mchunk_size));
        snprintf(next, sizeof(next), "%p", chunk->tcache.next);
        snprintf(key, sizeof(key), "%p", chunk->tcache.key);
    }

    printf("| %-19s | %-19s | %-28s | %-19s | %-19s |\n", address, prev_size, size, next, key);
}

void print_tcache(tcache_perthread_struct *tcache)
{
    for (int i = 0; i < TCACHE_MAX_BINS; i++) {
        if (tcache->counts[i] == 0)
            continue;

        int start_size = 8 + 16 * i + 1;
        int end_size = start_size + 15;
        if (i == 0)
            start_size = 0;

        tcache_entry *entry = tcache->entries[i];

        char bin[18];
        char size[22];
        char count[12];
        char head[26];
        char key[26];

        snprintf(bin, sizeof(bin), "TCACHE BIN #%d", i);
        snprintf(size, sizeof(size), "SIZE: %d - %d", start_size, end_size);
        snprintf(count, sizeof(count), "COUNT: %d", tcache->counts[i]);
        snprintf(head, sizeof(head), "HEAD: %p", entry);
        snprintf(key, sizeof(key), "KEY: %p", tcache);

        printf("+====================+========================+==============+============================+============================+\n");
        printf("| %-18s | %-22s | %-12s | %-26s | %-26s |\n", bin, size, count, head, key);
        printf("+====================+========================+==============+============================+============================+\n");
        printf("| ADDRESS             | PREV_SIZE (-0x10)   | SIZE (-0x08)                 | next (+0x00)        | key (+0x08)         |\n");
        printf("+---------------------+---------------------+------------------------------+---------------------+---------------------+\n");

        for (int j = 0; j < tcache->counts[i]; j++) {
            print_chunk(CHUNKOF(entry), tcache);
            if (!is_mapped(entry))
                break;
            entry = entry->next;
        }

        printf("+----------------------------------------------------------------------------------------------------------------------+\n\n");
    }
}
