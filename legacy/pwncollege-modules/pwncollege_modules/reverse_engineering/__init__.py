import tempfile
import pathlib
import pwnshop
import random
import struct
import time
import sys
import os

verify_outputs_path = pathlib.Path(__file__).parent / "verify_outputs"
verify_inputs_path = pathlib.Path(__file__).parent / "verify_inputs"


#
# Utility
#

SPRITES = {
    "c": ( 6, 4, bytes.fromhex("20205f5f5f20202f205f5f7c7c20285f5f20205c5f5f5f7c") ),
    "I": ( 5, 5, bytes.fromhex("205f5f5f207c5f205f7c207c207c20207c207c207c5f5f5f7c") ),
    "M": ( 8, 5, bytes.fromhex("205f5f20205f5f207c20205c2f20207c7c207c5c2f7c207c7c207c20207c207c7c5f7c20207c5f7c") ),
    "G": ( 7, 5, bytes.fromhex("20205f5f5f5f20202f205f5f5f7c7c207c20205f207c207c5f7c207c205c5f5f5f5f7c") ),
}

class Sprite:
    #pylint:disable=too-many-positional-arguments
    def __init__(self, data=None, width=None, height=None, letter=None, color=(0,0,0)):
        if letter:
            self.width, self.height, data = SPRITES[letter]
        else:
            self.width, self.height = width, height

        assert len(data) == self.width * self.height
        self.lines = [ data[j*self.width:(j+1)*self.width] for j in range(self.height) ]

        if isinstance(color, random.Random):
            self.color = [ color.randrange(1, 256), color.randrange(1, 256), color.randrange(1, 256) ]
        else:
            self.color = color

def lines_file_to_img(path, newlines=False):
    img = Image.from_file(path)
    return img.width, img.height, img.render(newlines), img.pixels

class Image:
    NEWLINE = b"\x1b[38;2;000;000;000m\n\x1b[0m"

    def __init__(self, width, height):
        self.pixels = [ list(b"\0\0\0 "*width) for _ in range(height) ]

    @property
    def height(self):
        return len(self.pixels)
    @property
    def width(self):
        return len(self.pixels[0])//4 if self.pixels else 0
    @property
    def data(self):
        return b"".join(bytes(line) for line in self.pixels)

    def apply_sprite(self, sprite, x, y):
        for j in range(sprite.height):
            for i in range(sprite.width):
                pixel = sprite.color + [ sprite.lines[j][i] ]
                self.pixels[y+j][x*4+i*4:x*4+i*4+4] = pixel

    def render(self, newlines=False):
        rendered = (self.NEWLINE if newlines else b"").join(b"".join(
            b"\x1b[38;2;%03d;%03d;%03dm%c\x1b[0m" % (
                line[i+0],
                line[i+1],
                line[i+2],
                line[i+3]
            )
            for i in range(0, len(line), 4)
        ) for line in self.pixels)
        return rendered

    @classmethod
    def from_file(cls, path):
        data = open(path, "rb").readlines()
        img = Image(width=len(data[0])//4, height=len(data))
        for dl,il in zip(data, img.pixels):
            il[:] = dl.strip(b"\n")
        return img

    @classmethod
    def from_sprite(cls, spr):
        img = Image(width=spr.width, height=spr.height)
        img.apply_sprite(spr, 0, 0)
        return img

    def print(self):
        sys.stdout.buffer.write(self.render(True))
        print()

def decolor(colored):
    bw = b""
    for i in range(colored.index(b"\x1b"), len(colored), 24):
        if colored[i:i+1] != b"\x1b":
            break
        bw += colored[i+19:i+20]
    return bw

class CIMGBase(pwnshop.Challenge, register=False):
    TEMPLATE_PATH = "cimg.c"
    OPTIMIZATION_FLAG = "-Os"
    PIE = False
    print_greeting = False
    vbuf_in_main = False
    vbuf_in_constructor = True
    constant_goodbye = False
    static_win_function_variables = False
    win_message = None
    version = 0
    width = None
    height = None
    initial_won_value = 1

    directives = { }
    partial_source = False
    hide_directives = False

    # easy wins for randomization
    magic_chars = "cIMG"
    magic_str = None
    magic_int = None
    version_bitwidth = 16
    width_bitwidth = 8
    height_bitwidth = 8
    directives_bitwidth = 32

    target_img = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text_coords = [ ]
        self.text_sprites = [ ]
        self.edge_sprites = [ ]

    def deploy(self, dst_dir, **kwargs):
        if self.partial_source:
            kwargs["src"] = True
            self.hide_directives = True
            self.render()
        return super().deploy(dst_dir, **kwargs)

    def randomize_bitwidths(self):
        self.version_bitwidth = self.random.choice([8, 16, 32, 64])
        self.width_bitwidth = self.random.choice([8, 16, 32, 64])
        self.height_bitwidth = self.random.choice([8, 16, 32, 64])
        self.directives_bitwidth = self.random.choice([8, 16, 32, 64])

    def randomize_magic(self):
        valid_headers = [ "CIMG", "CNNR", "CONR", "CNMG", "CMAG", "CMGE" ]
        replacements = { "C": "cC[(<{", "I": "iI1|/!;:l", "M": "mM", "G": "gG6", "N": "nN%~", "O": "oO0@", "A": "aA4@", "E": "eE3", "R": "rR" }

        v = self.random.choice(valid_headers)
        v = (
            self.random.choice(replacements[v[0]]) +
            self.random.choice(replacements[v[1]]) +
            self.random.choice(replacements[v[2]]) +
            self.random.choice(replacements[v[3]])
        )

        if self.magic_chars not in (False, None):
            self.magic_chars = v
        elif self.magic_str not in (False, None):
            self.magic_str = v
        else:
            self.magic_int = struct.unpack("<I", v.encode('l1'))[0]

    def build_image(self, magic=None, version=None, width=None, height=None, directives=None, data=None):
        fmts = { 8: "B", 16: "<H", 32: "<I", 64: "<Q" }

        s = b""
        if self.magic_chars or self.magic_str:
            s += magic or (self.magic_chars or self.magic_str).encode('l1')
        else:
            s += magic or struct.pack("<I", self.magic_int)

        if self.version:
            s += struct.pack(fmts[self.version_bitwidth], version or self.version)

        if self.width or width is not None:
            s += struct.pack(
                fmts[self.width_bitwidth],
                width if width is not None else self.width if type(self.width) is int else self.target_img.width
            )
            s += struct.pack(
                fmts[self.height_bitwidth],
                height if height is not None else self.height if type(self.height) is int else self.target_img.height
            )

        if self.directives:
            s += struct.pack(fmts[self.directives_bitwidth], len(directives)) + b"".join(directives)

        if data:
            s += data

        return s

    def make_target_image(self, text="cIMG", width=None, height=None):
        min_width = sum(SPRITES[c][0] for c in text) + len(text)-1 + 4 # borders
        min_height = max(SPRITES[c][1] for c in text) + 4 # borders

        width = self.random.randrange(min_width + 3, 80) if width is None else width
        height = self.random.randrange(min_height + 3, 24) if height is None else height

        assert width >= min_width
        assert height >= min_height

        pixels = Image(height=height, width=width)

        # make the border
        top = Sprite(data=b"."+b"-"*(width-2)+b".", width=width, height=1, color=[255,255,255])
        side = Sprite(data=b"|"*(height-2), width=1, height=height-2, color=[255,255,255])
        bottom = Sprite(data=b"'"+b"-"*(width-2)+b"'", width=width, height=1, color=[255,255,255])
        self.edge_sprites = [ top, side, bottom ]

        pixels.apply_sprite(top, 0, 0)
        pixels.apply_sprite(side, 0, 1)
        pixels.apply_sprite(side, width-1, 1)
        pixels.apply_sprite(bottom, 0, height-1)

        self.text_sprites = [ Sprite(letter=c, color=self.random) for c in text ]

        cursor_x = 2
        for n,c in enumerate(self.text_sprites):
            max_x = width - 2 - sum(cc.width for cc in self.text_sprites[n:]) - (len(self.text_sprites)-n)
            min_y = height - 2 - c.height

            x = self.random.randrange(cursor_x, max_x+1)
            y = self.random.randrange(2, min_y)

            self.text_coords.append([x,y])

            pixels.apply_sprite(c, x, y)
            cursor_x = x + c.width + 1

        # pixels.print()
        return pixels


class CIMGBasePython(pwnshop.PythonChallenge, register=False):
    TEMPLATE_PATH = "cimg.py"

    def __init__(self, *args, **kwargs):
        if not hasattr(self, "mirror_class"):
            raise AttributeError("Missing 'mirror' class attribute")
        self.mirror = self.mirror_class(*args, **kwargs)
        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.mirror, name)

    def verify(self, **kwargs):
        return self.mirror.__class__.verify(self, **kwargs)

    def run_challenge(self, *args, **kwargs):
        if "cmd_args" in kwargs:
            # For some reason PythonChallenge has a different interface than Challenge
            kwargs["argv"] = kwargs.pop("cmd_args")
        return super().run_challenge(*args, **kwargs)


class CIMGMagicNumber(CIMGBase):
    win_function = True
    OPTIMIZATION_FLAG = "-O0"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.randomize_magic()

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image())
            assert self.flag in process.readall()

        with self.run_challenge(**kwargs) as process:
            process.write(b"ABCD")
            assert self.flag not in process.readall()

        t = tempfile.mktemp()
        with open(t+".cimg", "wb") as o:
            o.write(self.build_image())
        with open(t, "wb") as o:
            o.write(b"NOPE")
        with self.run_challenge(cmd_args=[t+".cimg"], **kwargs) as process:
            assert self.flag in process.readall()
        with self.run_challenge(cmd_args=[t], **kwargs) as process:
            assert self.flag not in process.readall()


class CIMGMagicNumberPython(CIMGBasePython):
    mirror_class = CIMGMagicNumber


class CIMGMagicInt(CIMGBase):
    win_function = True
    magic_chars = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.randomize_magic()

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image())
            assert self.flag in process.readall()

        with self.run_challenge(**kwargs) as process:
            process.write(b"ABCD")
            assert self.flag not in process.readall()


class CIMGMagicIntPython(CIMGBasePython):
    mirror_class = CIMGMagicInt


class CIMGVersion(CIMGBase):
    win_function = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.version = self.random.randrange(10, 256)
        self.randomize_magic()
        self.randomize_bitwidths()

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image())
            assert self.flag in process.readall()

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(version=self.version+1))
            assert self.flag not in process.readall()


class CIMGVersionPython(CIMGBasePython):
    mirror_class = CIMGVersion


class CIMGDimensions(CIMGBase):
    win_function = True
    version = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.width = self.random.randint(40, 80)
        self.height = self.random.randint(10, 24)
        self.randomize_magic()
        self.randomize_bitwidths()

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(data=b"\x00" * (self.width * self.height)))
            assert self.flag in process.readall()

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=self.width-1, data=b"\x00" * (self.width * self.height)))
            result = process.readall()
            assert self.flag not in result
            assert b"Incorrect width" in result

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(data=b"\x00" * (self.width * self.height - 1)))
            result = process.readall()
            assert self.flag not in result
            assert b"Failed to read" in result and b"data" in result


class CIMGDimensionsPython(CIMGBasePython):
    mirror_class = CIMGDimensions


class CIMGAscii(CIMGBase):
    win_function = True
    version = 1
    assert_ascii = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.width = self.random.randint(40, 80)
        self.height = self.random.randint(10, 24)
        self.randomize_bitwidths()

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(data=b"A" * (self.width * self.height)))
            assert self.flag in process.readall()

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(data=b"\x00" * (self.width * self.height)))
            result = process.readall()
            assert self.flag not in result
            assert b"Invalid character" in result


class CIMGAsciiPython(CIMGBasePython):
    mirror_class = CIMGAscii


class CIMGDisplay(CIMGBase):
    version = 1
    width = True
    height = True
    assert_ascii = True
    display = True
    check_num_nonspace = 275
    win_function = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.randomize_bitwidths()

    def verify(self, **kwargs):
        output = (verify_outputs_path / "cIMG.txt").read_bytes()

        lines = output.splitlines()
        width, height = len(lines[0]), len(lines)
        data = output.replace(b"\n", b"")

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=width, height=height, data=data))
            result = process.readall()
            assert result.startswith(output)
            assert self.flag in result

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=width, height=height, data=b" "*width*height))
            assert self.flag not in process.readall()


class CIMGDisplayPython(CIMGBasePython):
    mirror_class = CIMGDisplay


class CIMGColor(CIMGBase):
    version = 2
    width = True
    height = True
    assert_ascii = True
    display = True
    color = True
    check_asu_maroon = True
    win_function = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.width = self.random.randint(20, 80)
        self.height = self.random.randint(20, 24)
        self.check_num_nonspace = self.width*self.height
        self.randomize_bitwidths()

    def verify(self, **kwargs):
        data = b"\x8c\x1d\x40A"*self.width*self.height

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=self.width, height=self.height, data=data))
            result = process.readall()
            assert self.flag in result


class CIMGColorPython(CIMGBasePython):
    mirror_class = CIMGColor


class CIMGFramebufferBase(CIMGBase, register=False):
    version = 2
    width = True
    height = True
    assert_ascii = True
    display = True
    framebuffer = True
    color = True
    randomized_target_img = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.randomized_target_img:
            self.target_img = self.make_target_image()
        else:
            self.target_img = Image.from_file(verify_inputs_path / "cIMG-colored")

        self.check_framebuffer = self.target_img.render(False) + b"\0"
        assert b'"' not in self.check_framebuffer, "Framebuffer must not contain quotes"

class CIMGFramebuffer(CIMGFramebufferBase):
    win_function = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=self.target_img.width, height=self.target_img.height, data=self.target_img.data))
            result = process.readall()
            assert result.startswith(self.target_img.render(True))
            assert self.flag in result

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(height=0, width=0))
            assert self.flag not in process.readall()

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=self.target_img.width, height=self.target_img.height, data=b"#"*self.target_img.width*self.target_img.height*4))
            assert self.flag not in process.readall()

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=self.target_img.width, height=self.target_img.height, data=b"\0\0\0"+self.target_img.data[3:]))
            result = process.readall()
            assert self.flag not in result


class CIMGFramebufferMini(CIMGFramebuffer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.target_img = Image(height=1, width=4)
        self.target_img.apply_sprite(Sprite(data=b"c", width=1, height=1, color=self.random), 0, 0)
        self.target_img.apply_sprite(Sprite(data=b"I", width=1, height=1, color=self.random), 1, 0)
        self.target_img.apply_sprite(Sprite(data=b"M", width=1, height=1, color=self.random), 2, 0)
        self.target_img.apply_sprite(Sprite(data=b"G", width=1, height=1, color=self.random), 3, 0)

        self.check_framebuffer = self.target_img.render(False) + b"\0"

class CIMGDirectivesBase(CIMGFramebufferBase):
    version = 3
    randomized_directives = False
    sprite_tiling = False
    sprite_transparency = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.randomize_directives()

    def randomize_directives(self):
        if self.randomized_directives:
            for k,i in zip(self.directives, self.random.sample(range(2**16), len(self.directives))):
                self.directives[k] = i

    def emit_patch(self, x, y, img):
        return struct.pack("<H", self.directives["RENDER_PATCH"]) + bytes([x, y, img.width, img.height]) + img.data

    def emit_create_sprite(self, sid, w, h, data):
        return struct.pack("<H", self.directives["CREATE_SPRITE"]) + bytes([sid, w, h]) + data

    def emit_render_sprite(self, sid, r, g, b, x, y, i=None, j=None, a=None):
        s = struct.pack("<H", self.directives["RENDER_SPRITE"]) + bytes([sid, r, g, b, x, y])
        if self.sprite_tiling:
            s += bytes([i,j])
        if self.sprite_transparency:
            s += bytes([a])
        return s

class CIMGDirectives(CIMGDirectivesBase):
    directives = { "RENDER_FRAME": 1 }
    win_function = True
    randomized_directives = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=self.target_img.width, height=self.target_img.height, directives=[
                struct.pack("<H", self.directives["RENDER_FRAME"]) + self.target_img.data
            ]))
            result = process.readall()
            assert result.startswith(self.target_img.render(True))
            assert self.flag in result

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=self.target_img.width, height=self.target_img.height, directives=[
                struct.pack("<H", self.directives["RENDER_FRAME"]) + self.target_img.data.replace(b"\xff", b"\x42")
            ]))
            result = process.readall()
            assert self.flag not in result

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=self.target_img.width, height=self.target_img.height, directives=[
                struct.pack("<H", self.directives["RENDER_FRAME"]) + b"#"*self.target_img.width*self.target_img.height*4
            ]))
            assert self.flag not in process.readall()

class CIMGPatch(CIMGDirectivesBase):
    check_total_data = 1340
    directives = { "RENDER_FRAME": 1, "RENDER_PATCH": 2}
    win_function = True
    randomized_directives = True

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=self.target_img.width, height=self.target_img.height, directives=[
                struct.pack("<H", self.directives["RENDER_FRAME"]) + self.target_img.data
            ]))
            result = process.readall()
            assert result.startswith(self.target_img.render(True))
            assert self.flag not in result

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=self.target_img.width, height=self.target_img.height, directives=[
                self.emit_patch(0, 0, self.target_img)
            ]))
            result = process.readall()
            assert result.startswith(self.target_img.render(True))
            assert self.flag not in result

        #with self.run_challenge(**kwargs) as process:
        #   top_patch = Image.from_file(verify_inputs_path / "patch-top")
        #   bottom_patch = Image.from_file(verify_inputs_path / "patch-bottom")
        #   left_patch = Image.from_file(verify_inputs_path / "patch-left")
        #   right_patch = Image.from_file(verify_inputs_path / "patch-right")
        #   middle_patch = Image.from_file(verify_inputs_path / "patch-cIMG")

        #   process.write(self.build_image(width=self.target_img.width, height=self.target_img.height, directives=[
        #       self.emit_patch(0, 0, top_patch),
        #       self.emit_patch(0, self.target_img.height-1, bottom_patch),
        #       self.emit_patch(0, 1, left_patch),
        #       self.emit_patch(self.target_img.width-1, 1, right_patch),
        #       self.emit_patch(23, 9, middle_patch),
        #   ]))
        #   result = process.readall()
        #   assert result.startswith(self.target_img.render(True))
        #   assert self.flag not in result

        with self.run_challenge(**kwargs) as process:
            top_patch = Image.from_sprite(self.edge_sprites[0])
            left_patch = Image.from_sprite(self.edge_sprites[1])
            right_patch = Image.from_sprite(self.edge_sprites[1])
            bottom_patch = Image.from_sprite(self.edge_sprites[2])
            letter_c = Image.from_sprite(self.text_sprites[0])
            letter_I = Image.from_sprite(self.text_sprites[1])
            letter_M = Image.from_sprite(self.text_sprites[2])
            letter_G = Image.from_sprite(self.text_sprites[3])

            process.write(self.build_image(width=self.target_img.width, height=self.target_img.height, directives=[
                self.emit_patch(0, 0, top_patch),
                self.emit_patch(0, self.target_img.height-1, bottom_patch),
                self.emit_patch(0, 1, left_patch),
                self.emit_patch(self.target_img.width-1, 1, right_patch),
                self.emit_patch(self.text_coords[0][0], self.text_coords[0][1], letter_c),
                self.emit_patch(self.text_coords[1][0], self.text_coords[1][1], letter_I),
                self.emit_patch(self.text_coords[2][0], self.text_coords[2][1], letter_M),
                self.emit_patch(self.text_coords[3][0], self.text_coords[3][1], letter_G),
            ]))
            result = process.readall()
            # WHY??? assert result.startswith(self.target_img.render(True))
            assert self.flag in result

class CIMGPatch1337(CIMGPatch):
    check_total_data = 1337
    randomized_directives = False
    randomized_target_img = False

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            top_patch = Image.from_file(verify_inputs_path / "patch-top")
            bottom_patch = Image.from_file(verify_inputs_path / "patch-bottom")
            left_patch = Image.from_file(verify_inputs_path / "patch-left")
            right_patch = Image.from_file(verify_inputs_path / "patch-right")
            letter_c = Image.from_file(verify_inputs_path / "patch-c")
            letter_I = Image.from_file(verify_inputs_path / "patch-I")
            letter_M_left = Image.from_file(verify_inputs_path / "patch-M-left")
            letter_M_middle = Image.from_file(verify_inputs_path / "patch-M-middle")
            letter_M_right = Image.from_file(verify_inputs_path / "patch-M-right")
            letter_G = Image.from_file(verify_inputs_path / "patch-G")

            process.write(self.build_image(width=self.target_img.width, height=self.target_img.height, directives=[
                self.emit_patch(0, 0, top_patch),
                self.emit_patch(0, self.target_img.height-1, bottom_patch),
                self.emit_patch(0, 1, left_patch),
                self.emit_patch(self.target_img.width-1, 1, right_patch),

                self.emit_patch(23, 10, letter_c),
                self.emit_patch(30, 9, letter_I),
                self.emit_patch(36, 9, letter_M_left),
                self.emit_patch(39, 10, letter_M_middle),
                self.emit_patch(41, 9, letter_M_right),
                self.emit_patch(45, 9, letter_G),
            ]))
            result = process.readall()
            assert result.startswith(self.target_img.render(True))
            assert self.flag in result

class CIMGPatchNoWin(CIMGPatch):
    win_function = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.check_framebuffer = None

    def verify(self, **kwargs):
        pass

class CIMGSprite(CIMGDirectivesBase):
    check_framebuffer = lines_file_to_img(verify_inputs_path / "cIMG-colored", False)[-2] + b"\0"
    check_total_data = 400
    sprites = True
    directives = { "RENDER_FRAME": 1, "RENDER_PATCH": 2, "CREATE_SPRITE": 3, "RENDER_SPRITE": 4 }
    win_function = True
    randomized_target_img = False

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=80, height=24, directives=[
                struct.pack("<H", self.directives["CREATE_SPRITE"]) + bytes([0, 2, 2]) + b"####",
                struct.pack("<H", self.directives["RENDER_SPRITE"]) + bytes([0, 0xff, 0xff, 0xff, 78, 1]),
            ]))
            result = process.readall()
            assert result.count(b"#") == 4
            assert all(line.count(b"#") == 2 for line in result.split(b"\n")[1:3])
            assert self.flag not in result

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=self.target_img.width, height=self.target_img.height, directives=[
                self.emit_create_sprite(0,        1,  1,  b"."),
                self.emit_create_sprite(1,        74, 1,  b"-"*74),
                self.emit_create_sprite(2,        1,  22, b"|"*22),
                self.emit_create_sprite(3,        1,  1,  b"'"),
                self.emit_create_sprite(ord('c'), 6,  4,  SPRITES['c'][-1]),
                self.emit_create_sprite(ord('I'), 5,  5,  SPRITES['I'][-1]),
                self.emit_create_sprite(ord('M'), 8,  5,  SPRITES['M'][-1]),
                self.emit_create_sprite(ord('G'), 7,  5,  SPRITES['G'][-1]),

                self.emit_render_sprite(0,        0xff, 0xff, 0xff, 0,  0),
                self.emit_render_sprite(0,        0xff, 0xff, 0xff, 75, 0),
                self.emit_render_sprite(3,        0xff, 0xff, 0xff, 0,  23),
                self.emit_render_sprite(3,        0xff, 0xff, 0xff, 75, 23),
                self.emit_render_sprite(1,        0xff, 0xff, 0xff, 1,  0),
                self.emit_render_sprite(1,        0xff, 0xff, 0xff, 1,  23),
                self.emit_render_sprite(2,        0xff, 0xff, 0xff, 0,  1),
                self.emit_render_sprite(2,        0xff, 0xff, 0xff, 75, 1),
                self.emit_render_sprite(ord('c'), 0xff, 0x00, 0x00, 23, 10),
                self.emit_render_sprite(ord('I'), 0x00, 0xff, 0x00, 30, 9),
                self.emit_render_sprite(ord('M'), 0x00, 0x00, 0xff, 36, 9),
                self.emit_render_sprite(ord('G'), 0x80, 0x80, 0x80, 45, 9),
            ]))
            result = process.readall()
            assert self.flag in result

class CIMGSpriteParse(CIMGSprite):
    check_total_data = None
    check_framebuffer = None
    win_function = False

    def verify(self, **kwargs):
        pass

class CIMGSpriteTiled(CIMGDirectivesBase):
    version = 4
    check_total_data = 285
    sprites = True
    sprite_tiling = True
    sprite_transparency = True
    directives = { "RENDER_FRAME": 1, "RENDER_PATCH": 2, "CREATE_SPRITE": 3, "RENDER_SPRITE": 4 }
    win_function = True

    randomized_target_img = False

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=80, height=24, directives=[
                self.emit_create_sprite(0, 1, 1, b"#"),
                self.emit_render_sprite(0, 0xff, 0xff, 0xff, 0, 0, 80, 24, ord(' ')),
            ]))
            result = process.readall()
            assert all(line.count(b"#") == 80 for line in result.split(b"\n")[:24])
            assert self.flag not in result

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=80, height=24, directives=[
                self.emit_create_sprite(1, 2, 2, b"####"),
                self.emit_render_sprite(1, 0xff, 0xff, 0xff, 0, 2, 5, 5, ord(' ')),
            ]))
            result = process.readall()
            assert result.count(b"#") == 100
            assert result.split(b"\n")[0].count(b"#") == 0
            assert all(line.count(b"#") == 10 for line in result.split(b"\n")[2:12])
            assert self.flag not in result

        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(directives=[
                self.emit_create_sprite(0,        1, 1, b"."),
                self.emit_create_sprite(1,        1, 1, b"-"),
                self.emit_create_sprite(2,        1, 1, b"|"),
                self.emit_create_sprite(3,        1, 1, b"'"),
                self.emit_create_sprite(4,        1, 1, b" "),
                self.emit_create_sprite(ord('c'), 6, 4, SPRITES['c'][-1]),
                self.emit_create_sprite(ord('I'), 5, 5, SPRITES['I'][-1]),
                self.emit_create_sprite(ord('M'), 8, 5, SPRITES['M'][-1]),
                self.emit_create_sprite(ord('G'), 7, 5, SPRITES['G'][-1]),

                self.emit_render_sprite(0,        0xff, 0xff, 0xff, 0,  0,  76, 1,  0),
                self.emit_render_sprite(3,        0xff, 0xff, 0xff, 0,  23, 76, 1,  0),
                self.emit_render_sprite(1,        0xff, 0xff, 0xff, 1,  0,  74, 24, 0),
                self.emit_render_sprite(2,        0xff, 0xff, 0xff, 0,  1,  76, 22, 0),
                self.emit_render_sprite(4,        0xff, 0xff, 0xff, 1,  1,  74, 22, 0),
                self.emit_render_sprite(ord('c'), 0xff, 0x00, 0x00, 23, 10, 1,  1,  ord(" ")),
                self.emit_render_sprite(ord('I'), 0x00, 0xff, 0x00, 30, 9,  1,  1 , ord(" ")),
                self.emit_render_sprite(ord('M'), 0x00, 0x00, 0xff, 36, 9,  1,  1 , ord(" ")),
                self.emit_render_sprite(ord('G'), 0x80, 0x80, 0x80, 45, 9,  1,  1 , ord(" ")),
            ]))
            result = process.readall()
            assert self.flag in result

class CIMGSpriteLoad(CIMGDirectivesBase):
    version = 4
    sprites = True
    sprite_tiling = True
    sprite_transparency = True
    unsafe_sprite_loading = True
    directives = { "RENDER_FRAME": 1, "RENDER_PATCH": 2, "CREATE_SPRITE": 3, "RENDER_SPRITE": 4, "LOAD_SPRITE": 5 }
    win_function = False

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=76, height=1, directives=[
                struct.pack("<H", self.directives["LOAD_SPRITE"]) + bytes([0, len(self.flag.strip()), 1]) + b"/flag".ljust(255, b'\0'),
                struct.pack("<H", self.directives["RENDER_SPRITE"]) + bytes([0, 0xff, 0xff, 0xff, 0, 0, 1, 1, ord(" ") ])
            ]))
            result = process.readall()
            assert self.flag.strip() in decolor(result)

class CIMGAnimateUnsafe(CIMGBase):
    version = 4
    width = True
    height = True
    assert_ascii = True
    display = True
    framebuffer = True
    color = True
    sprites = True
    sprite_tiling = True
    sprite_transparency = True
    unsafe_clear = True
    directives = { "RENDER_FRAME": 1, "RENDER_PATCH": 2, "CREATE_SPRITE": 3, "RENDER_SPRITE": 4, "LOAD_SPRITE": 5, "FLUSH": 6, "SLEEP": 7 }
    win_function = False

    def verify(self, **kwargs):
        d = tempfile.mkdtemp()
        with open(d+"/clear", "w") as o:
            o.write("#!/bin/sh\n/bin/cat /flag\n")
        os.chmod(d+"/clear", 0o755)
        with self.run_challenge(env={"PATH": d}, **kwargs) as process:
            process.write(self.build_image(width=10, height=10, directives=[
                struct.pack("<H", self.directives["FLUSH"]) + b"\x01"
            ]))
            result = process.readall()
            assert self.flag in result


class CIMGAnimate(CIMGAnimateUnsafe):
    unsafe_clear = False

    def verify(self, **kwargs):
        start = time.time()
        with self.run_challenge(**kwargs) as process:
            process.write(self.build_image(width=10, height=10, directives=[
                struct.pack("<H", self.directives["SLEEP"]) + struct.pack("<I", 500),
                struct.pack("<H", self.directives["SLEEP"]) + struct.pack("<I", 500),
                struct.pack("<H", self.directives["SLEEP"]) + struct.pack("<I", 1100),
            ]))
            process.readall()
        end = time.time()
        assert end - start > 2

class CIMGQuestUnpatched(CIMGAnimate):
    magic_str = "cIMG"
    magic_chars = None
    directive_code_if = True

class CIMGQuestUnpatchedSwitch(CIMGQuestUnpatched):
    directive_code_if = False

class CIMGQuestPatched(CIMGAnimate):
    directives = { "RENDER_FRAME": 7, "RENDER_PATCH": 6, "CREATE_SPRITE": 5, "RENDER_SPRITE": 4, "LOAD_SPRITE": 3, "FLUSH": 2, "SLEEP": 1 }
    magic_chars = "CNNR"

    def verify(self, **kwargs):
        pass
