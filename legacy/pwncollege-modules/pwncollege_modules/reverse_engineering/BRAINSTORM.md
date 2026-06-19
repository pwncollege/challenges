/*
level 1: read, magic number
- look at decompilation, see a read and strcmp
*/
struct cimg_header {
    char magic_number[4];
} cimg;
read(0, &cimg, sizeof(cimg));
assert(strcmp(cimg.magic_number, "CIMG") == 0);

/*
level 2: check version
- figure out how to input non-ascii characters
*/
struct cimg_header {
    char magic_number[4];
    uint16_t version;
} cimg;
read(0, &cimg, sizeof(cimg));
assert(strcmp(cimg.magic_number, "CIMG") == 0 && cimg.version == 1);

/*
level 3: read based on width and height
- the size of the file is dynamic, based on the width and height
  - not only are you determining what to set width and height to, but also that you need way more (whatever) bytes to read in
*/
struct cimg_header {
    char magic_number[4];
    uint16_t version;
    uint16_t width;
    uint16_t height;
};
struct cimg {
    struct cimg_header header;
    uint8_t *data;
} cimg;
read(0, &cimg, sizeof(cimg));
assert(strcmp(cimg.magic_number, "CIMG") == 0 && cimg.version == 1 && cimg.width == 42 && cimg.height == 42);

uint8_t data[42 * 42];
assert(read(0, data, cimg.width * cimg.height) == cimg.width * cimg.height);
cimg.data = data;

/*
level 4: a real ascii-cimg
- we have control flow and a function call
  - Sure it's two concepts... but seriously, it doesn't matter
*/
struct cimg_header {
    char magic_number[4];
    uint16_t version;
    uint16_t width;
    uint16_t height;
};
struct cimg {
    struct cimg_header header;
    uint8_t *data;
} cimg;

void display(struct cimg *cimg) {
    for (int i = 0; i < cimg->header.height; i++) {
        for (int j = 0; j < cimg->header.width; j++) {
            putchar(cimg->data[i * cimg->header.width + j]);
        }
        putchar('\n');
    }
}

read(0, &cimg, sizeof(cimg));
assert(strcmp(cimg.magic_number, "CIMG") == 0 && cimg.version == 1 && cimg.width == 42 && cimg.height == 42);

uint8_t data[42 * 42];
assert(read(0, data, cimg.width * cimg.height) == cimg.width * cimg.height);
cimg.data = data;

for (int i = 0; i < cimg.height * cimg.width; i++) {
    assert(cimg.data[i] >= 0x20 && cimg.data[i] <= 0x7e);
}

/*
level 5: compare with a reference
*/
// /challenge/check < my.cimg
expected_cimg = open("/challenge/expected_output", "rb").read()
assert subprocess.check_output("/challenge/cimg", input=sys.stdin.buffer.read(), encoding="ascii").strip() == expected_cimg

/*
more thoughts:
- we could handle color with ansii escape codes
  - v2: your pixel isnt 1 ascii byte, it's 4 bytes (3 for color, 1 for ascii)
  - interested nested state
- cursor
  - maybe with v2 of the cimg spec, now with state!
  - global/"ctx" state that changes with time
  - way more effecient than this lame 4 bytes per pixel thing
  - multiple state-transformations
  - state possibilities:
    - what is my current color?
    - what is the position of my cursor?
  - v3: interpret data as a series of instructions
    - 1 byte opcode
    - opcode0: print ascii character of my operand0: \x00A\x00B\x00C\x00D => ABCD
    - opcode1: set my color to operand0: \x01\xFF\xFF\xFF\x00A => white A
    - we can enforce this with .cimg file size restrictions
  - v4: opcode2: repeated-ascii
    - operand0 is 2-bytes: how many times to repeat
    - operand1 is 1-byte: what ascii character to repeat
    - \x02\x05\x00A => AAAAA
  - v5: opcode3: repeated-multi-ascii
    - operand0 is 1-byte: how many times to repeat
    - operand1 is 1-byte: how many ascii characters to repeat
    - operand2 is operand-1-many-bytes: what ascii character(s) to repeat
    - \x03\x03\x02AB => ABABAB
  - v6: opcode4: add rule
    - \x04A\xFF\xFF\xFF => if I see A, set my color to white
    - we can enforce this with .cimg file size restrictions
    - have a cool ABABABA pattern or whatever
  - v7: opcode5: new frame
    - operand0 is 2-byte: delay in ms
    - operand1 is 2-byte: x
    - operand2 is 2-byte: y
    - \x05\x64\x00\x00\x00\x00\x00 => wait 100ms, then reset my cursor to top left
    - probably you might do a \x02\xff\xff\x20 to clear the screen
  - v8: opcode6: go to frame
    - operand0 is 2-byte: frame number
    - \x06\x00\x01 => go to frame 1

Challenge Design:
- provide a .cimg file (should we use argv[1] and demand .cimg extension?)
- asserts on metadata
- restrict file size
- asserts to reach bug states? reason about finding bugs while reversing, thinking about edge cases
  - opcode0 with invalid ascii character
  - opcode2 with invalid ascii character
  - repeated multi-ascii with invalid ascii characters
  - go to a frame that doesn't exist
  - set cursor to invalid position
*/


echo -e "\033[38;2;R;G;BmYour text here\033[0m"
