#define _GNU_SOURCE 1

#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include <assert.h>
#include <libgen.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <sys/signal.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <sys/sendfile.h>
#include <sys/prctl.h>
#include <sys/personality.h>
#include <arpa/inet.h>

void read_exact(int fd, void *dst, int size, char *msg, int exitcode)
{
    int n = read(fd, dst, size);
    if (n != size)
    {
        fprintf(stderr, msg);
        fprintf(stderr, "\n");
        exit(exitcode);
    }
}

struct cimg_header
{
    char magic_number[4];
    uint16_t version;
    uint8_t width;
    uint8_t height;
    uint32_t remaining_directives;
} __attribute__((packed));

typedef struct
{
    uint8_t ascii;
} pixel_bw_t;
#define COLOR_PIXEL_FMT "\x1b[38;2;%03d;%03d;%03dm%c\x1b[0m"
typedef struct
{
    uint8_t r;
    uint8_t g;
    uint8_t b;
    uint8_t ascii;
} pixel_color_t;
typedef pixel_color_t pixel_t;

typedef struct
{
    union
    {
        char data[24];
        struct term_str_st
        {
            char color_set[7];   // \x1b[38;2;
            char r[3];          // 255
            char s1;            // ;
            char g[3];          // 255
            char s2;            // ;
            char b[3];          // 255
            char m;            // m
            char c;             // X
            char color_reset[4];     // \x1b[0m
        } str;
    };
} term_pixel_t;

struct cimg_sprite
{
    uint8_t height;
    uint8_t width;
    pixel_bw_t *data;
};

struct cimg
{
    struct cimg_header header;
    unsigned num_pixels;
    term_pixel_t *framebuffer;
    struct cimg_sprite sprites[256];
};

#define CIMG_NUM_PIXELS(cimg) ((cimg)->header.width * (cimg)->header.height)
#define CIMG_DATA_SIZE(cimg) (CIMG_NUM_PIXELS(cimg) * sizeof(pixel_t))
#define CIMG_FRAMEBUFFER_PIXELS(cimg) ((cimg)->header.width * (cimg)->header.height)
#define CIMG_FRAMEBUFFER_SIZE(cimg) (CIMG_FRAMEBUFFER_PIXELS(cimg) * sizeof(term_pixel_t))

#include "cimg-handlers.c" // YOU DON'T GET THIS FILE!

void display(struct cimg *cimg, pixel_t *data)
{
    for (int i = 0; i < cimg->header.height; i++)
    {
        write(1, cimg->framebuffer+i*cimg->header.width, sizeof(term_pixel_t)*cimg->header.width);
        write(1, "\x1b[38;2;000;000;000m\n\x1b[0m", 24);
    }
}

struct cimg *initialize_framebuffer(struct cimg *cimg)
{
    cimg->num_pixels = CIMG_FRAMEBUFFER_PIXELS(cimg);
    cimg->framebuffer = malloc(CIMG_FRAMEBUFFER_SIZE(cimg)+1);
    if (cimg->framebuffer == NULL)
    {
        puts("ERROR: Failed to allocate memory for the framebuffer!");
        exit(-1);
    }
    for (int idx = 0; idx < cimg->num_pixels; idx += 1)
    {
        char emit_tmp[24+1];
        snprintf(emit_tmp, sizeof(emit_tmp), "\x1b[38;2;%03d;%03d;%03dm%c\x1b[0m", 255, 255, 255, ' ');
        memcpy(cimg->framebuffer[idx].data, emit_tmp, 24);

    }

    return cimg;
}

void __attribute__ ((constructor)) disable_buffering()
{
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 1);
}

int main(int argc, char **argv, char **envp)
{

    struct cimg cimg = { 0 };
    cimg.framebuffer = NULL;
    int won = 1;

    if (argc > 1)
    {
        if (strcmp(argv[1]+strlen(argv[1])-5, ".cimg"))
        {
            printf("ERROR: Invalid file extension!");
            exit(-1);
        }
        dup2(open(argv[1], O_RDONLY), 0);
    }

    read_exact(0, &cimg.header, sizeof(cimg.header), "ERROR: Failed to read header!", -1);

    if (strncmp(cimg.header.magic_number, "cIMG", sizeof(cimg.header.magic_number)))
    {
        puts("ERROR: Invalid magic number!");
        exit(-1);
    }

    if (cimg.header.version != 4)
    {
        puts("ERROR: Unsupported version!");
        exit(-1);
    }

    initialize_framebuffer(&cimg);

    while (cimg.header.remaining_directives--)
    {
        uint16_t directive_code;
        read_exact(0, &directive_code, sizeof(directive_code), "ERROR: Failed to read &directive_code!", -1);

        switch (directive_code)
        {
        case 1:
            handle_1(&cimg);
            break;
        case 2:
            handle_2(&cimg);
            break;
        case 3:
            handle_3(&cimg);
            break;
        case 4:
            handle_4(&cimg);
            break;
        case 5:
            handle_5(&cimg);
            break;
        case 6:
            handle_6(&cimg);
            break;
        case 7:
            handle_7(&cimg);
            break;
        default:
            fprintf(stderr, "ERROR: invalid directive_code %ux\n", directive_code);
            exit(-1);
        }
    }
    display(&cimg, NULL);

}