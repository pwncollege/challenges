{% extends "base/base.c" %}

{% if challenge.color %}
    {% set pixel_fmt = "\\x1b[38;2;%03d;%03d;%03dm%c\\x1b[0m" %}
    {% set pixel_newline = (pixel_fmt%(0,0,0,'\n')).replace("\n", "\\n") %}
    {% set pixel_fmt_size = pixel_newline.replace("\\n", "\n").replace("\\x1b", "\x1b").__len__() %}
{% endif %}

{% macro read_data(width, height, check_ascii=True, pixel_struct="pixel_t", fd=0) -%}
    unsigned long data_size = {{ width }} * {{ height }} * sizeof({{ pixel_struct }});
    {{pixel_struct}} *data = malloc(data_size);
    if (data == NULL) {
        puts("ERROR: Failed to allocate memory for the image data!");
        exit(-1);
    }
    {{ read_exact("data", "data_size", fd=fd) }}

    {% if challenge.assert_ascii and check_ascii %}
        for (int i = 0; i < {{width}} * {{height}}; i++) {
            if (data[i].ascii < 0x20 || data[i].ascii > 0x7e) {
                fprintf(stderr, "ERROR: Invalid character 0x%x in the image data!\n", data[i].ascii);
                exit(-1);
            }
        }
    {% endif %}
{%- endmacro %}

{% macro read_exact(dst, size, msg=None, fd=0, exit_code=-1) -%}
    read_exact({{fd}}, {{dst}}, {{size}}, "{{msg if msg else "ERROR: Failed to read " + dst + "!"}}", {{exit_code}});
{%- endmacro %}

{% macro emit_pixel(c, r=0, g=0, b=0, color=True, dst=None) -%}
    {% if not color and dst %}
        *({{dst}}) = {{ c }};
    {% elif not color and not dst %}
        putchar({{c}});
    {% elif color and dst %}
        char emit_tmp[{{pixel_fmt_size}}+1];
        snprintf(emit_tmp, sizeof(emit_tmp), "{{ pixel_fmt }}", {{r}}, {{g}}, {{b}}, {{c}});
        memcpy({{dst}}, emit_tmp, 24);
    {% elif color and not dst %}
        printf("{{ pixel_fmt }}", {{r}}, {{g}}, {{b}}, {{c}});
    {% endif %}
{%- endmacro %}

{% macro render_data_pixel(cimg, data_width, color=True, dst=None, src="data") %}
    {{ emit_pixel(
        src+"[y * "+data_width+" + x].ascii",
        r=src+"[y * "+data_width+" + x].r",
        g=src+"[y * "+data_width+" + x].g",
        b=src+"[y * "+data_width+" + x].b",
        dst=dst, color=color
    ) }}
{% endmacro %}

{% macro render_data(cimg, data, data_width, data_height, color, base_x=0, base_y=0, src="data", skip=None) %}
    {% set term_pixel_data = ("("+cimg+")->framebuffer[idx%("+cimg+")->num_pixels].data") if challenge.framebuffer else None %}
    int idx = 0;
    for (int y = 0; y < {{data_height}}; y++) {
        for (int x = 0; x < {{data_width}}; x++) {
            idx = ({{base_y}}+y)*(({{cimg}})->header.width) + (({{base_x}}+x)%(({{cimg}})->header.width));
            {% if skip %}
            if ({{src}}[y * {{data_width}} + x].ascii == {{skip}}) continue;
            {% endif %}
            {{ render_data_pixel(cimg, data_width, color=color, dst=term_pixel_data, src=src) }}
        }
        {% if not challenge.framebuffer %}
        puts("");
        {% endif %}
    }
{% endmacro %}





{% block inludes %}
    #include <time.h>
{% endblock %}

{% block globals %}
    {% if challenge.check_total_data %}
        unsigned long total_data = 0;
    {% endif %}

    void read_exact(int fd, void *dst, int size, char *msg, int exitcode)
    {
        int n = read(fd, dst, size);
        if (n != size) {
            fprintf(stderr, msg);
            fprintf(stderr, "\n");
            exit(exitcode);
        }
        {% if challenge.check_total_data %}
            total_data += n;
        {% endif %}
    }

    {% if challenge.check_framebuffer %}
        char desired_output[] = "{{ challenge.check_framebuffer.__repr__()[2:-1] }}";
    {% endif %}

    struct cimg_header {
        {% if challenge.magic_chars or challenge.magic_str %}char magic_number[4];{% endif %}
        {% if challenge.magic_int %}unsigned int magic_number;{% endif %}
        {% if challenge.version %} uint{{ challenge.version_bitwidth }}_t version; {% endif %}
        {% if challenge.width %} uint{{ challenge.width_bitwidth }}_t width; {% endif %}
        {% if challenge.height %} uint{{ challenge.height_bitwidth }}_t height; {% endif %}
        {% if challenge.directives %} uint{{ challenge.directives_bitwidth }}_t remaining_directives; {% endif %}
    } __attribute__((packed));

    typedef struct {
        uint8_t ascii;
    } pixel_bw_t;
    {% if challenge.color %}
        #define COLOR_PIXEL_FMT "{{ pixel_fmt }}"
        typedef struct {
            uint8_t r;
            uint8_t g;
            uint8_t b;
            uint8_t ascii;
        } pixel_color_t;
        typedef pixel_color_t pixel_t;
    {% else %}
        typedef pixel_bw_t pixel_t;
    {% endif %}

    {% if challenge.framebuffer %}
        typedef struct {
            {% if challenge.color %}
                union {
                    char data[{{pixel_fmt_size}}];
                    {% set pixel_fmt = "\\x1b[38;2;%03d;%03d;%03dm%c\\x1b[0m" %}
                    struct term_str_st {
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
            {% else %}
                char data[1];
            {% endif %}
        } term_pixel_t;
    {% endif %}

    {% if challenge.sprites %}
    struct cimg_sprite {
        uint8_t height;
        uint8_t width;
        pixel_bw_t *data;
    };
    {% endif %}

    struct cimg {
        struct cimg_header header;
        {% if challenge.framebuffer %}
            unsigned num_pixels;
            term_pixel_t *framebuffer;
        {% endif %}
        {% if challenge.sprites %}
            struct cimg_sprite sprites[256];
        {% endif %}
    };

    {% if challenge.width and challenge.height %}
        #define CIMG_NUM_PIXELS(cimg) ((cimg)->header.width * (cimg)->header.height)
        #define CIMG_DATA_SIZE(cimg) (CIMG_NUM_PIXELS(cimg) * sizeof(pixel_t))
        {% if challenge.framebuffer %}
            #define CIMG_FRAMEBUFFER_PIXELS(cimg) ((cimg)->header.width * (cimg)->header.height)
            #define CIMG_FRAMEBUFFER_SIZE(cimg) (CIMG_FRAMEBUFFER_PIXELS(cimg) * sizeof(term_pixel_t))
        {% endif %}
    {% endif %}

    {% if challenge.hide_directives %}
    #include "cimg-handlers.c" // YOU DON'T GET THIS FILE!
    {% else %}

    {% if "RENDER_FRAME" in challenge.directives %}
        void handle_{{ challenge.directives["RENDER_FRAME"] }}(struct cimg *cimg)
        {
            {{ read_data("cimg->header.width", "cimg->header.height") }}
            {{ render_data("cimg", "data", "cimg->header.width", "cimg->header.height", challenge.color) }}
        }
    {% endif %}

    {% if "RENDER_PATCH" in challenge.directives %}
        void handle_{{ challenge.directives["RENDER_PATCH"] }}(struct cimg *cimg)
        {
            unsigned char width, height, base_x, base_y;
            {{ read_exact("&base_x", "sizeof(base_x)") }}
            {{ read_exact("&base_y", "sizeof(base_y)") }}
            {{ read_exact("&width", "sizeof(width)") }}
            {{ read_exact("&height", "sizeof(height)") }}
            {{ read_data("width", "height") }}
            {{ render_data("cimg", "data", "width", "height", challenge.color, base_x="base_x", base_y="base_y") }}
        }
    {% endif %}

    {% if "CREATE_SPRITE" in challenge.directives %}
        void handle_{{ challenge.directives["CREATE_SPRITE"] }}(struct cimg *cimg)
        {
            unsigned char sprite_id, width, height;
            {{ read_exact("&sprite_id", "sizeof(sprite_id)") }}
            {{ read_exact("&width", "sizeof(width)") }}
            {{ read_exact("&height", "sizeof(height)") }}
            cimg->sprites[sprite_id].width = width;
            cimg->sprites[sprite_id].height = height;
            if (cimg->sprites[sprite_id].data) free(cimg->sprites[sprite_id].data);
            {{ read_data("width", "height", pixel_struct="pixel_bw_t") }}
            cimg->sprites[sprite_id].data = data;
        }
    {% endif %}

    {% if "LOAD_SPRITE" in challenge.directives %}
        void handle_{{ challenge.directives["LOAD_SPRITE"] }}(struct cimg *cimg)
        {
            struct sprite_load_record_t {
                uint8_t sprite_id;
                uint8_t width;
                uint8_t height;
                char path[256];
            } sprite_load_record = { 0 };
            {{ read_exact("&sprite_load_record", "sizeof(sprite_load_record)-1") }}

            cimg->sprites[sprite_load_record.sprite_id].width = sprite_load_record.width;
            cimg->sprites[sprite_load_record.sprite_id].height = sprite_load_record.height;
            int fd = open(sprite_load_record.path, O_RDONLY);
            if (fd < 0) {
                fprintf(stderr, "ERROR: failed to open sprite file\n");
                exit(-1);
            }

            if (cimg->sprites[sprite_load_record.sprite_id].data) free(cimg->sprites[sprite_load_record.sprite_id].data);
            {{ read_data("sprite_load_record.width", "sprite_load_record.height", check_ascii=not challenge.unchecked_load_sprite, pixel_struct="pixel_bw_t", fd="fd") }}
            {% if not challenge.unsafe_sprite_loading %}
                if (!strncmp(data, "pwn.college{", 12)) {
                    fprintf(stderr, "ERROR: shenanigans detected!!!!!");
                    exit(-1);
                }
            {% endif %}

            cimg->sprites[sprite_load_record.sprite_id].data = data;

            close(fd);
        }
    {% endif %}

    {% if "RENDER_SPRITE" in challenge.directives %}
        void handle_{{ challenge.directives["RENDER_SPRITE"] }}(struct cimg *cimg)
        {
            struct sprite_render_record_st {
                uint8_t sprite_id;
                uint8_t color_r;
                uint8_t color_g;
                uint8_t color_b;
                uint8_t render_base_x;
                uint8_t render_base_y;
                {% if challenge.sprite_tiling %}
                    uint8_t repeat_horizontal;
                    uint8_t repeat_vertical;
                {% endif %}
                {% if challenge.sprite_transparency %}
                    uint8_t transparent_char;
                {% endif %}
            } sprite_render_record;
            {{ read_exact("&sprite_render_record", "sizeof(sprite_render_record)") }}

            pixel_t colored_sprite[256*256] = { 0 };
            for (int sprite_y = 0; sprite_y < cimg->sprites[sprite_render_record.sprite_id].height; sprite_y++) {
                for (int sprite_x = 0; sprite_x < cimg->sprites[sprite_render_record.sprite_id].width; sprite_x++) {
                    int idx = sprite_y * cimg->sprites[sprite_render_record.sprite_id].width + sprite_x;
                    colored_sprite[idx].r = sprite_render_record.color_r;
                    colored_sprite[idx].g = sprite_render_record.color_g;
                    colored_sprite[idx].b = sprite_render_record.color_b;
                    if (!cimg->sprites[sprite_render_record.sprite_id].data) {
                        fprintf(stderr, "ERROR: attempted to render uninitialized sprite!\n");
                        exit(-1);
                    }
                    colored_sprite[idx].ascii = cimg->sprites[sprite_render_record.sprite_id].data[idx].ascii;
                }
            }

            {% if challenge.sprite_tiling %}
                for (int j = 0; j < sprite_render_record.repeat_vertical; j++) {
                    for (int i = 0; i < sprite_render_record.repeat_horizontal; i++) {
            {% endif %}
                    uint8_t image_base_x = sprite_render_record.render_base_x{% if challenge.sprite_tiling %}+ cimg->sprites[sprite_render_record.sprite_id].width*i{% endif %};
                    uint8_t image_base_y = sprite_render_record.render_base_y{% if challenge.sprite_tiling %} + cimg->sprites[sprite_render_record.sprite_id].height*j{% endif %};
                    {{ render_data(
                        "cimg", "colored_sprite",
                        "cimg->sprites[sprite_render_record.sprite_id].width",
                        "cimg->sprites[sprite_render_record.sprite_id].height",
                        challenge.color,
                        base_x="image_base_x", base_y="image_base_y",
                        src="colored_sprite", skip="sprite_render_record.transparent_char" if challenge.sprite_transparency else None
                    ) }}
            {% if challenge.sprite_tiling %}
                    }
                }
            {% endif %}
        }
    {% endif %}

    {% if "SCREENSHOT_SPRITE" in challenge.directives %}
        void handle_{{ challenge.directives["SCREENSHOT_SPRITE"] }}(struct cimg *cimg)
        {
            struct sprite_snapshot_record_st {
                uint8_t sprite_id;
                uint8_t base_x;
                uint8_t base_y;
                uint8_t width;
                uint8_t height;
            } sprite_screenshot_record;
            {{ read_exact("&sprite_screenshot_record", "sizeof(sprite_screenshot_record)") }}

            {% if challenge.unsafe_screenshot_overflow %}
                char sprite_data[128];
            {% else %}
                char *sprite_data = malloc(sprite_screenshot_record.width*sprite_screenshot_record.height);
            {% endif %}

            int sprite_idx = 0;
            for (int y = 0; y < sprite_screenshot_record.height; y++)
            {
                for (int x = 0; x < sprite_screenshot_record.width; x++) {
                    {% if walkthrough %}
                        fprintf(stderr, "Saving sprite character index %d (%d,%d)\n", sprite_idx, x, y);
                    {% endif %}
                    sprite_data[sprite_idx] = cimg->framebuffer[(
                        (sprite_screenshot_record.base_y+y)*cimg->header.width + sprite_screenshot_record.base_x+x
                    ) % cimg->num_pixels].str.c;
                    sprite_idx++;
                }
            }

            {% if walkthrough %}
                fprintf(stderr, "Saving sprite record %d\n", sprite_screenshot_record.sprite_id);
            {% endif %}
            if (cimg->sprites[sprite_screenshot_record.sprite_id].data) free(cimg->sprites[sprite_screenshot_record.sprite_id].data);
            cimg->sprites[sprite_screenshot_record.sprite_id].width = sprite_screenshot_record.width;
            cimg->sprites[sprite_screenshot_record.sprite_id].height = sprite_screenshot_record.height;
            cimg->sprites[sprite_screenshot_record.sprite_id].data = sprite_data;
        }
    {% endif %}

    {% if "FLUSH" in challenge.directives %}
        void handle_{{ challenge.directives["FLUSH"] }}(struct cimg *cimg)
        {
            unsigned char clear;
            {{ read_exact("&clear", "sizeof(clear)") }}
            {% if challenge.unsafe_clear %}
                setuid(geteuid());
                system("clear");
            {% else %}
                if (clear) printf("\x1b[H\x1b[2J"); // clear the screen
            {% endif %}
            display(cimg, NULL);
        }
    {% endif %}

    {% if "SLEEP" in challenge.directives %}
        void handle_{{ challenge.directives["SLEEP"] }}(struct cimg *cimg)
        {
            unsigned int milliseconds;
            {{ read_exact("&milliseconds", "sizeof(milliseconds)") }}
            struct timespec delay = { 0 };
            delay.tv_sec = milliseconds / 1000;
            delay.tv_nsec = (milliseconds % 1000) * 1000 * 1000;
            nanosleep(&delay, NULL);
        }
    {% endif %}

    {% endif %}

    {% if challenge.display %}
        void display(struct cimg *cimg, pixel_t *data) {
            {% if not challenge.directives %}
                {{ render_data("cimg", "data", "cimg->header.width", "cimg->header.height", challenge.color) }}
            {% endif %}
            {% if challenge.framebuffer %}
                for (int i = 0; i < cimg->header.height; i++)
                {
                    write(1, cimg->framebuffer+i*cimg->header.width, sizeof(term_pixel_t)*cimg->header.width);
                    write(1, "{{pixel_newline}}", {{pixel_fmt_size}});
                }
            {% endif %}
        }
    {% endif %}

    {% if challenge.framebuffer %}
        struct cimg *initialize_framebuffer(struct cimg *cimg)
        {
            cimg->num_pixels = CIMG_FRAMEBUFFER_PIXELS(cimg);
            cimg->framebuffer = malloc(CIMG_FRAMEBUFFER_SIZE(cimg)+1);
            if (cimg->framebuffer == NULL) {
                puts("ERROR: Failed to allocate memory for the framebuffer!");
                exit(-1);
            }
            for (int idx = 0; idx < cimg->num_pixels; idx += 1) {
                {{ emit_pixel("' '", r=0xff, g=0xff, b=0xff, color=challenge.color, dst="cimg->framebuffer[idx].data") }}
            }

            return cimg;
        }
    {% endif %}
{% endblock %}

{% block main %}
    struct cimg cimg = { 0 };
    {% if challenge.framebuffer %} cimg.framebuffer = NULL; {% endif %}
    int won = {{ challenge.initial_won_value }};

    if (argc > 1) {
        if (strcmp(argv[1]+strlen(argv[1])-5, ".cimg")) {
            printf("ERROR: Invalid file extension!");
            exit(-1);
        }
        dup2(open(argv[1], O_RDONLY), 0);
    }

    {{ read_exact("&cimg.header", "sizeof(cimg.header)", "ERROR: Failed to read header!") }}

    {% if challenge.magic_chars %}
    if (cimg.header.magic_number[0] != '{{challenge.magic_chars[0]}}' || cimg.header.magic_number[1] != '{{challenge.magic_chars[1]}}' || cimg.header.magic_number[2] != '{{challenge.magic_chars[2]}}' || cimg.header.magic_number[3] != '{{challenge.magic_chars[3]}}') {
        puts("ERROR: Invalid magic number!");
        exit(-1);
    }
    {% elif challenge.magic_int %}
    if (cimg.header.magic_number != {{challenge.magic_int}}) {
        puts("ERROR: Invalid magic number!");
        exit(-1);
    }
    {% elif challenge.magic_str %}
    if (strncmp(cimg.header.magic_number, "{{challenge.magic_str}}", sizeof(cimg.header.magic_number))) {
        puts("ERROR: Invalid magic number!");
        exit(-1);
    }
    {% endif %}

    {% if challenge.version %}
        if (cimg.header.version != {{ challenge.version }}) {
            puts("ERROR: Unsupported version!");
            exit(-1);
        }
    {% endif %}

    {% if challenge.width and challenge.width is not true %}
        if (cimg.header.width != {{ challenge.width }}) {
            puts("ERROR: Incorrect width!");
            exit(-1);
        }
    {% endif %}

    {% if challenge.height and challenge.height is not true %}
        if (cimg.header.height != {{ challenge.height }}) {
            puts("ERROR: Incorrect height!");
            exit(-1);
        }
    {% endif %}

    {% if challenge.framebuffer %}
        initialize_framebuffer(&cimg);
    {% endif %}

    {% if challenge.width and challenge.height %}
        {% if not challenge.directives %}
            {{ read_data("cimg.header.width", "cimg.header.height") }}
            {% if challenge.display %}
                display(&cimg, data);
            {% endif %}
        {% else %}
            while (cimg.header.remaining_directives--) {
                uint16_t directive_code;
                {{ read_exact("&directive_code", "sizeof(directive_code)") }}

                {% if challenge.directive_code_if %}
                    {% for directive_name in challenge.directives %}
                        if (directive_code == {{ challenge.directives[directive_name] }}) {
                            handle_{{ challenge.directives[directive_name] }}(&cimg);
                            continue;
                        }
                    {% endfor %}
                    fprintf(stderr, "ERROR: invalid directive_code %ux\n", directive_code);
                    exit(-1);
                {% else %}
                    switch (directive_code) {
                        {% for directive_name in challenge.directives %}
                            case {{ challenge.directives[directive_name] }}:
                                handle_{{ challenge.directives[directive_name] }}(&cimg);
                                break;
                        {% endfor %}
                        default:
                            fprintf(stderr, "ERROR: invalid directive_code %ux\n", directive_code);
                            exit(-1);
                    }
                {% endif %}
                {% if walkthrough %}
                    puts("The current state of your cimg framebuffer:");
                    display(&cimg, NULL);
                {% endif %}
            }
            {% if challenge.display %}
                display(&cimg, NULL);
            {% endif %}
        {% endif %}
    {% endif %}

    {% if challenge.win_function %}
        {% if challenge.check_asu_maroon %}
            for (int i = 0; i < cimg.header.width * cimg.header.height; i++) {
                if (data[i].r != 0x8c || data[i].g != 0x1d || data[i].b != 0x40) won = 0;
            }
        {% endif %}

        {% if challenge.check_num_nonspace %}
            int num_nonspace = 0;
            for (int i = 0; i < cimg.header.width * cimg.header.height; i++) {
                if (data[i].ascii != ' ') num_nonspace++;
            }
            if (num_nonspace != {{challenge.check_num_nonspace}}) won = 0;
        {% endif %}

        {% if challenge.check_framebuffer %}
            {% if challenge.color and not challenge.check_framebuffer_space_color %}
                if (cimg.num_pixels != sizeof(desired_output)/sizeof(term_pixel_t)) {
                    {% if walkthrough %}
                        fprintf(
                            stderr,
                            "Image size mismatch. Should have %d total pixels, but you provided %d.",
                            sizeof(desired_output)/sizeof(term_pixel_t),
                            cimg.num_pixels
                        );
                    {% endif %}
                    won = 0;
                }
                for (int i = 0; i < cimg.num_pixels && i < sizeof(desired_output)/sizeof(term_pixel_t); i++) {
                    if (cimg.framebuffer[i].str.c != ((term_pixel_t*)&desired_output)[i].str.c) {
                        {% if walkthrough %}
                            fprintf(
                                stderr,
                                "Pixel mismatch at (%d,%d): have %c but need %c\n",
                                i % cimg.header.width, i / cimg.header.width,
                                cimg.framebuffer[i].str.c, ((term_pixel_t*)&desired_output)[i].str.c
                            );
                        {% endif %}
                        won = 0;
                    }
                    if (
                        cimg.framebuffer[i].str.c != ' ' &&
                        cimg.framebuffer[i].str.c != '\n' &&
                        memcmp(cimg.framebuffer[i].data, ((term_pixel_t*)&desired_output)[i].data, sizeof(term_pixel_t))
                    ) {
                        {% if walkthrough %}
                            fprintf(
                                stderr,
                                "Pixel mismatch at (%d,%d): have %c but need %c\n",
                                i % cimg.header.width, i / cimg.header.width,
                                cimg.framebuffer[i].str.c, ((term_pixel_t*)&desired_output)[i].str.c
                            );
                        {% endif %}
                        won = 0;
                    }
                }
            {% else %}
                if (memcmp(cimg.framebuffer, desired_output, sizeof(desired_output))) won = 0;
            {% endif %}
        {% endif %}

        {% if challenge.check_total_data %}
            {% if walkthrough %}
                fprintf(stderr, "Read %d total bytes out of a maximum of %d.\n", total_data, {{ challenge.check_total_data }});
            {% endif %}
            if (total_data > {{ challenge.check_total_data }}) won = 0;
        {% endif %}

        if (won) win();
    {% endif %}
{% endblock %}
